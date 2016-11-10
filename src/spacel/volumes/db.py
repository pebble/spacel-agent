import logging

from botocore.exceptions import ClientError

logger = logging.getLogger('spacel')


class VolumeDb(object):
    """
    Tracks volume sets in DynamoDb.
    """

    def __init__(self, clients, meta):
        self._dynamo = clients.dynamodb()
        self._ec2 = clients.ec2()
        self._instance_id = meta.instance_id
        self._az = meta.az
        self._table_name = '%s-volumes' % meta.orbit


    def get_assignment(self, volume):
        """
        Get assigned volume.
        :param volume: Volume descriptor.
        :return: DynamoDb item for assigned volume (can be `None`).
        """
        volume_items = self._get_volume_items(volume)

        # Index volumes records:
        volumes_by_index = {}
        attached_volumes = {}
        uncreated_volumes = set(range(volume.count))
        for volume_item in volume_items:
            volume_index = int(volume_item['index']['N'])
            volume_assignment = volume_item.get('assignment')
            if volume_assignment:
                assigned_instance = volume_assignment['S']
                if assigned_instance == self._instance_id:
                    logger.debug('Discovered existing assignment %d.',
                                 volume_index)
                    return volume_item
                attached_volumes[assigned_instance] = volume_index

            volumes_by_index[volume_index] = volume_item
            uncreated_volumes.remove(volume_index)

        # If possible, create a new volume:
        for volume_index in uncreated_volumes:
            logger.debug('Acquiring new volume %d...', volume_index)
            try:
                new_item = self._create_volume(volume, volume_index)
                logger.debug('Acquired new volume volume %d...', volume_index)
                return new_item
            except ClientError:  # pragma: no cover
                logger.warn('Unable to create volume record %d.', volume_index)

        # Look for orphaned volumes:
        instance_ids = attached_volumes.keys()
        instance_status = self._ec2.describe_instances(InstanceIds=instance_ids)
        dead_instances = dict(attached_volumes)
        for reservation in instance_status.get('Reservations', ()):
            for instance in reservation.get('Instances', ()):
                dead_instance_id = instance['InstanceId']
                state = instance['State']['Name'].lower()
                if state == 'pending' or state == 'running':
                    del dead_instances[dead_instance_id]
                    continue

                volume_index = attached_volumes[dead_instance_id]
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
            except ClientError:  # pragma: no cover
                pass

        # Every volume is created and assigned to a running instance.
        # TODO: choose a victim like EIP?
        return None

    def save(self, volume_item, initial_item={}):
        volume_key = {
            'label': volume_item['label'],
            'index': volume_item['index'],
        }

        update_values = {}
        for update_key in ('volume_id', 'snapshot_id', 'az'):
            new_value = volume_item.get(update_key)
            if new_value != initial_item.get(update_key):
                update_values[':%s' % update_key] = new_value

        if not update_values:
            return

        update_fields = ['{0} = :{0}'.format(update_key[1:]) for update_key in
                         update_values.keys()]
        update_expression = 'SET ' + ', '.join(update_fields)
        update_values[':instance_id'] = {'S': self._instance_id}

        logger.debug('Updating item %s', volume_key)
        self._dynamo.update_item(
            TableName=self._table_name,
            Key=volume_key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=update_values,
            ConditionExpression='assignment = :instance_id')

    def _get_volume_items(self, volume):
        volume_keys = [self._volume_key(volume.label, index)
                       for index in range(volume.count)]
        volume_batch = self._dynamo.batch_get_item(RequestItems={
            self._table_name: {'Keys': volume_keys, 'ConsistentRead': True}})
        return volume_batch.get('Responses', {}).get(self._table_name, ())

    def _create_volume(self, volume, volume_index):
        new_item = self._volume_key(volume.label, volume_index)
        new_item['assignment'] = {'S': self._instance_id}
        new_item['az'] = {'S': self._az}
        self._dynamo.put_item(
            TableName=self._table_name,
            Item=new_item,
            ConditionExpression='attribute_not_exists(service)')
        return new_item

    def _assign_volume(self, volume, volume_index, old_instance_id):
        self._dynamo.update_item(
            TableName=self._table_name,
            Key=self._volume_key(volume.label, volume_index),
            UpdateExpression='SET assignment = :instance_id',
            ConditionExpression='assignment = :old_instance',
            ExpressionAttributeValues={
                ':instance_id': {'S': self._instance_id},
                ':old_instance': {'S': old_instance_id}
            })

    @staticmethod
    def _volume_key(label, index):
        return {
            'label': {'S': label},
            'index': {'N': str(index)},
        }
