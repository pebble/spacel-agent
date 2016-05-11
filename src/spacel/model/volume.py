import logging

logger = logging.getLogger('spacel')


class SpaceVolume(object):
    def __init__(self, label, params):
        self.label = label
        self.mount_point = params.get('mount_point', '/mnt/%s' % label)
        self.valid = True
        instance = params.get('instance')
        if instance is not None:
            self.count = 1
            self.encrypted = False
            try:
                self.instance = int(instance)
            except ValueError:
                self.instance = None
                self.valid = False
        else:
            self.instance = None
            self.count = params.get('count', 1)
            self.size = params.get('size', 4)
            self.encrypted = params.get('encrypted', False)
            self.type = params.get('type', 'gp2')

            self.iops = params.get('iops')
            if self.iops and self.type != 'io1':

                logger.warn('Provision IOPs with type %s, ignoring IOPS.',
                            self.type)
                self.iops = None
                self.valid = False
