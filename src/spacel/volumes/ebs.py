from botocore.exceptions import ClientError
import logging
from subprocess import check_output, CalledProcessError, STDOUT
import time

logger = logging.getLogger('spacel')


class EbsAttachment(object):
    """
    Creates/migrates/attaches EBS volumes to the local instance.
    """

    def __init__(self, clients, meta):
        self._ec2 = clients.ec2()
        self._az = meta.az
        self._instance_id = meta.instance_id

    def attach_volume(self, volume, volume_item):
        label = volume_item['label']['S']
        index = volume_item['index']['N']

        volume_id = volume_item.get('volume_id')
        if volume_id:
            volume_id = volume_id['S']
            logger.debug('Checking volume "%s".', volume_id)
            volume_description = self._describe_volume(volume_id)
            if volume_description:
                for attachment in volume_description['Attachments']:
                    attached_instance = attachment.get('InstanceId')
                    if attached_instance == self._instance_id:
                        logger.debug('Volume "%s" is already attached to %s.',
                                     volume_id, self._instance_id)
                        volume_item['device'] = {'S': attachment['Device']}
                        return volume_item

                    logger.debug('Volume "%s" is attached to another (%s)!',
                                 volume_id, attached_instance)
                    volume_waiter = self._ec2.get_waiter('volume_available')
                    volume_waiter.config.delay = 5
                    volume_waiter.wait(VolumeIds=[volume_id])
                    logger.debug('Volume "%s" released.', volume_id)

                volume_az = volume_description['AvailabilityZone']
                if volume_az == self._az:
                    logger.debug('Found usable %s in %s.', volume_id, self._az)
                    self._attach_volume(volume_item)
                    return volume_item

                logger.debug('Volume %s is in %s, migrating.', volume_id,
                             volume_az)
                snapshot = self._ec2.create_snapshot(VolumeId=volume_id)
                snapshot_id = snapshot['SnapshotId']
                self._ec2.create_tags(Resources=[snapshot_id],
                                      Tags=[
                                          {'Key': 'space-label',
                                           'Value': label},
                                          {'Key': 'space-index',
                                           'Value': index},
                                      ])

                logger.debug('Snapshot %s started...', snapshot_id)
                volume_item['snapshot_id'] = {'S': snapshot_id}

                self._ec2.get_waiter('snapshot_completed').wait(
                        SnapshotIds=[snapshot_id])
                logger.debug('Snapshot %s completed', snapshot_id)
                self._ec2.delete_volume(VolumeId=volume_id)

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
        if 'snapshot_id' in volume_item:
            volume_args['SnapshotId'] = volume_item['snapshot_id']['S']
        new_volume = self._ec2.create_volume(**volume_args)
        volume_id = new_volume['VolumeId']
        volume_item['volume_id'] = {'S': volume_id}

        self._ec2.create_tags(Resources=[volume_id],
                              Tags=[
                                  {'Key': 'space-label',
                                   'Value': label},
                                  {'Key': 'space-index',
                                   'Value': index},
                              ])

        self._ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
        logger.debug('Created %s in %s.', volume_id, self._az)
        self._attach_volume(volume_item)
        return volume_item

    def _describe_volume(self, volume_id):
        try:
            return self._ec2.describe_volumes(
                    VolumeIds=[volume_id])['Volumes'][0]
        except ClientError as e:
            if e.response['Error']['Code'] != 'InvalidVolume.NotFound':
                raise e
        return None

    def _attach_volume(self, volume_item):
        device = self._next_volume()
        try:
            volume_id = volume_item['volume_id']['S']
            logger.debug('Attaching %s to %s.', volume_id, device)
            self._ec2.attach_volume(
                    InstanceId=self._instance_id,
                    VolumeId=volume_id,
                    Device=device)
            volume_item['device'] = {'S': device}
        except ClientError as e:  # pragma: no cover
            if e.response['Error']['Code'] != 'VolumeInUse':
                raise e

        # Wait for block device to settle:
        for _ in range(300):
            try:
                blk = check_output(['/bin/lsblk', '-Pf', device], stderr=STDOUT)
                break
            except CalledProcessError:  # pragma: no cover
                time.sleep(0.1)
        logger.debug('Attached %s to %s', volume_id, device)

    @staticmethod
    def _next_volume():
        blk = check_output(['/bin/lsblk', '-pl'], stderr=STDOUT)
        devices = set()
        for blk_line in blk.split('\n'):
            device = blk_line.split(' ')[0]
            if not device.startswith('/'):
                continue
            devices.add(device)
        for device_index in range(24):
            device = '/dev/xvd%s' % (chr(ord('a') + device_index))
            if device not in devices:
                return device
        return None
