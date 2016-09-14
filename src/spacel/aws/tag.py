import logging

logger = logging.getLogger('spacel')


class TagWriter(object):
    def __init__(self, clients, meta):
        self._ec2 = clients.ec2()
        self._instance_id = meta.instance_id

    def update(self, manifest):
        tags = manifest.tags
        if not tags:
            logger.debug('Tags not set.')
            return

        my_tags = [{'Key': k, 'Value': v} for k, v in tags.items() if k and v]

        if my_tags:
            self._ec2.create_tags(
                Resources=[self._instance_id],
                Tags=my_tags)
