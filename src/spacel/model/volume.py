import logging

logger = logging.getLogger('spacel')


class SpaceVolume(object):
    def __init__(self, label, params):
        self.label = label
        self.count = params.get('count', 1)
        self.size = params.get('size', 4)
        self.encrypted = params.get('encrypted', False)
        self.type = params.get('type', 'gp2')
        self.mount_point = params.get('mount_point', '/mnt/%s' % label)

        self.iops = params.get('iops')
        if self.iops and self.type != 'io1':
            logger.warn('Provision IOPs with type %s, ignoring IOPS.',
                        self.type)
            self.iops = None
