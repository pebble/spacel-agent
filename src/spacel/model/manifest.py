import logging
from spacel.model.volume import SpaceVolume

logger = logging.getLogger('spacel')


class AgentManifest(object):
    def __init__(self, params={}):
        self.eips = params.get('eips', ())
        self.files = params.get('files', {})
        self.systemd = params.get('systemd', {})
        self.cf_signal = params.get('cloudformation_signal', {})
        self.volumes = {label: SpaceVolume(label, vol_params)
                        for label, vol_params in
                        params.get('volumes', {}).items()}
        self.elb = params.get('elb')
        self.healthcheck = params.get('healthcheck', {})

    @property
    def all_files(self):
        every_file = {}
        every_file.update(self.files)
        every_file.update(self.systemd)
        return every_file

    @property
    def valid(self):
        volume_ids = set()
        for volume in self.volumes.values():
            if not volume.valid:
                logger.warn('Invalid manifest: invalid volume.')
                return False
            instance = volume.instance
            if instance is not None:
                if instance in volume_ids:
                    logger.warn('Invalid manifest: duplicate instance volume.')
                    return False
                volume_ids.add(instance)

        if not self.systemd:
            logger.warn('Invalid manifest: no units provided.')
            return False

        return True
