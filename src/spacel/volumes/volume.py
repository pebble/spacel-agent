from copy import deepcopy
import logging

from spacel.volumes.db import VolumeDb
from spacel.volumes.ebs import EbsAttachment
from spacel.volumes.fs import DeviceMount

logger = logging.getLogger('spacel')


class VolumeBinder(object):
    def __init__(self, clients, meta):
        self._db = VolumeDb(clients, meta)
        self._ebs = EbsAttachment(clients, meta)
        self._fs = DeviceMount(meta)

    def attach(self, volume):
        if volume.instance is None:
            self._attach_ebs(volume)
        else:
            self._fs.mount_instance(volume)

    def _attach_ebs(self, volume):
        volume_item = self._db.get_assignment(volume)
        if not volume_item:
            return
        initial_volume = deepcopy(volume_item)
        self._ebs.attach_volume(volume, volume_item)
        self._fs.mount(volume, volume_item)
        if initial_volume != volume_item:
            self._db.save(volume_item, initial_volume)
