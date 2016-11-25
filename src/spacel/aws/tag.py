import logging

logger = logging.getLogger('spacel')


class InstanceTags(object):
    def __init__(self, clients, meta):
        self._ec2 = clients.ec2()
        self._instance_ids = [meta.instance_id]

    def get(self):
        instances = self._ec2.describe_instances(InstanceIds=self._instance_ids)
        for reservation in instances.get('Reservations', ()):
            for instance in reservation.get('Instances', ()):
                if instance['InstanceId'] == self._instance_ids[0]:
                    tags = instance.get('Tags', ())
                    return {tag['Key']: tag['Value'] for tag in tags}
        return {}

    def update(self, manifest):
        tags = manifest.tags
        if not tags:
            logger.debug('Tags not set.')
            return

        tags = [{'Key': k, 'Value': v} for k, v in tags.items() if k and v]
        if tags:
            self._ec2.create_tags(Resources=self._instance_ids, Tags=tags)
