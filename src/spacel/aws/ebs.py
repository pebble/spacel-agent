import logging
from botocore.exceptions import ClientError
from subprocess import check_output, CalledProcessError, STDOUT
import time
import os

logger = logging.getLogger('spacel')


class VolumeBinder(object):
    def __init__(self, clients, meta):
        self._dynamo = clients.dynamodb()
        self._ec2 = clients.ec2()
        self._instance_id = meta.instance_id
        self._az = meta.az
        self._volume_table = 'volumes'
        self._local_device = 'b'

    def bind(self, volume):
        volume_item = self._get_volume_assignment(volume)
        if not volume_item:
            logger.debug('Unable to assign volume.')
            return
        volume_id, attachment = self._get_volume(volume_item, volume)
        self._attach_volume(volume_id, attachment, volume.mount_point)

    def _get_volume_assignment(self, volume):
        # Query DynamoDb for volume records:
        volume_items = self._dynamo.batch_get_item(RequestItems={
            self._volume_table: {
                'Keys': [self._volume_key(volume.label, index)
                         for index in range(volume.count)],
                'ConsistentRead': True
            }
        }).get('Responses', {}).get(self._volume_table, ())

        # Index volumes records:
        volumes_by_index = {}
        uncreated_volumes = set(range(volume.count))
        attached_instances = {}
        for volume_item in volume_items:
            volume_index = int(volume_item['volume_index']['N'])

            volume_assignment = volume_item.get('assignment')
            if volume_assignment:
                assignment = volume_assignment['S']
                if assignment == self._instance_id:
                    logger.debug('Discovered existing assignment %d.',
                                 volume_index)
                    return volume_item
                attached_instances[assignment] = volume_index

            volumes_by_index[volume_index] = volume_item
            uncreated_volumes.remove(volume_index)

        # If possible, create a new volume:
        for volume_index in uncreated_volumes:
            logger.debug('Acquiring new volume volume %d...', volume_index)
            try:
                new_item = self._create_volume(volume, volume_index)
                logger.debug('Acquired new volume volume %d...', volume_index)
                return new_item
            except ClientError:  # pragma: no cover
                pass

        # Look for orphaned volumes:
        instance_ids = attached_instances.keys()
        instance_status = self._ec2.describe_instances(InstanceIds=instance_ids)
        dead_instances = dict(attached_instances)
        for reservation in instance_status.get('Reservations', ()):
            for instance in reservation.get('Instances', ()):
                dead_instance_id = instance['InstanceId']
                state = instance['State']['Name'].lower()
                if state == 'pending' or state == 'running':
                    del dead_instances[dead_instance_id]
                    continue

                volume_index = attached_instances[dead_instance_id]
                logger.debug('Instance %s (volume %d) is %s.', dead_instance_id,
                             volume_index, state)

                # If volume is in the current AZ, acquire immediately:
                if volumes_by_index[volume_index].get('az') == self._az:
                    try:
                        self._assign_volume(volume, volume_index,
                                            dead_instance_id)
                        return volumes_by_index[volume_index]
                    except ClientError:  # pragma: no cover
                        continue

        # Nothing dead in our AZ, what about other AZs:
        for dead_instance_id, volume_index in dead_instances.items():
            try:
                self._assign_volume(volume, volume_index, dead_instance_id)
                return volumes_by_index[volume_index]
            except ClientError:
                pass

        # Every volume is created and assigned to a running instance.
        # TODO: choose a victim like EIP?
        return None

    def _create_volume(self, volume, volume_index):
        new_item = self._volume_key(volume.label, volume_index)
        new_item['assignment'] = {'S': self._instance_id}
        new_item['az'] = {'S': self._az}
        self._dynamo.put_item(
                TableName=self._volume_table,
                Item=new_item,
                ConditionExpression='attribute_not_exists(service)')
        return new_item

    def _assign_volume(self, volume, volume_index, old_instance_id):
        self._dynamo.update_item(
                TableName=self._volume_table,
                Key=self._volume_key(volume.label, volume_index),
                UpdateExpression='SET assignment = :instance_id',
                ConditionExpression='assignment = :old_instance',
                ExpressionAttributeValues={
                    ':instance_id': {'S': self._instance_id},
                    ':old_instance': {'S': old_instance_id}
                })

    def _get_volume(self, volume_item, volume):
        snapshot_id = volume_item.get('snapshot_id')
        volume_id = volume_item.get('volume_id')
        new_snapshot = False
        if volume_id:
            volume_id = volume_id['S']
            logger.debug('Checking volume "%s".', volume_id)
            volume_description = self._describe_volume(volume_id)

            if volume_description:
                if volume_description['Attachments']:
                    for attachment in volume_description['Attachments']:
                        if attachment.get('InstanceId') == self._instance_id:
                            return volume_id, attachment

                    logger.warn('Volume %s is attached to another instance!',
                                volume_id)

                volume_az = volume_description['AvailabilityZone']
                if volume_az == self._az:
                    logger.debug('Found usable %s in %s.', volume_id, self._az)
                    return volume_id, None
                else:
                    logger.debug('Volume %s is in %s, snapshotting.',
                                 volume_id, volume_az)
                    snapshot = self._ec2.create_snapshot(VolumeId=volume_id)
                    snapshot_id = snapshot['SnapshotId']
                    logger.debug('Snapshot %s started...', snapshot_id)

                    self._ec2.get_waiter('snapshot_completed').wait(
                            SnapshotIds=[snapshot_id])
                    logger.debug('Snapshot %s completed', snapshot_id)
                    new_snapshot = True
                    self._ec2.delete_volume(VolumeId=volume_id)
                    # TODO: tag snapshot: label, volume_index

        logger.debug('Creating EBS volume in %s.', self._az)
        volume_args = {
            'Size': volume.size,
            'VolumeType': volume.type,
            'AvailabilityZone': self._az
        }
        if volume.iops:
            volume_args['Iops'] = volume.iops
        if volume.encrypted:
            volume_args['Encrypted'] = volume.encrypted
        if snapshot_id:
            volume_args['SnapshotId'] = snapshot_id
        new_volume = self._ec2.create_volume(**volume_args)
        volume_id = new_volume['VolumeId']
        self._ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
        logger.debug('Created %s in %s.', volume_id, self._az)

        update_expression = 'SET volume_id = :volume_id, az = :az'
        update_values = {
            ':volume_id': {'S': volume_id},
            ':az': {'S': self._az}
        }
        if new_snapshot:
            update_expression += ', snapshot_id = :snapshot_id'
            update_values[':snapshot_id'] = {'S': snapshot_id}

        self._dynamo.update_item(
                TableName=self._volume_table,
                Key=self._volume_key(volume_item['label']['S'],
                                     volume_item['volume_index']['N']),
                UpdateExpression=update_expression,
                ExpressionAttributeValues=update_values)
        return volume_id, None

    def _describe_volume(self, volume_id):
        try:
            return self._ec2.describe_volumes(
                    VolumeIds=[volume_id])['Volumes'][0]
        except ClientError as e:
            if e.response['Error']['Code'] != 'InvalidVolume.NotFound':
                raise e
        return None

    def _attach_volume(self, volume_id, attachment, mount_point):
        if not attachment:
            device = '/dev/xvd%s' % self._local_device
            self._local_device = chr(ord(self._local_device) + 1)
            try:
                logger.debug('Attaching %s to %s.', volume_id, device)
                self._ec2.attach_volume(
                        InstanceId=self._instance_id,
                        VolumeId=volume_id,
                        Device=device)
            except ClientError as e:
                if e.response['Error']['Code'] != 'VolumeInUse':
                    raise e
        else:
            device = attachment['Device']

        # Wait for block device to settle:
        while True:
            try:
                blk = check_output(['/bin/lsblk', '-Pf', device], stderr=STDOUT)
                break
            except CalledProcessError:
                time.sleep(0.1)

        if 'FSTYPE=""' in blk:
            logger.debug('Volume has no filesystem, creating...')
            check_output(['mkfs', '-t', 'ext4', device], stderr=STDOUT)
        else:
            logger.debug('Volume has filesystem, verifying...')
            check_output(['/sbin/e2fsck', '-f', device], stderr=STDOUT)
            check_output(['/sbin/resize2fs', device], stderr=STDOUT)

        with open('/etc/mtab') as mtab_in:
            existing_mount = [mtab_line for mtab_line in mtab_in.readlines()
                              if mtab_line.startswith(device)]

        if existing_mount:
            logger.debug('Volume %s is already mounted.', volume_id)
            # TODO: verify mount point matches
            return

        if not os.path.isdir(mount_point):
            os.mkdir(mount_point)

        logger.debug('Mounting %s at %s.', volume_id, mount_point)
        check_output(['/bin/mount', device, mount_point], stderr=STDOUT)
        check_output(['/bin/chmod', '777', mount_point], stderr=STDOUT)
        logger.debug('Mounted %s at %s.', volume_id, mount_point)

    @staticmethod
    def _volume_key(service, volume_index):
        return {
            'label': {'S': service},
            'volume_index': {'N': str(volume_index)},
        }
