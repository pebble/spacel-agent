import logging
import os
from subprocess import check_output, STDOUT

logger = logging.getLogger('spacel')


class DeviceMount(object):
    def __init__(self, meta):
        self.meta = meta

    def mount(self, volume, volume_item):
        device = volume_item['device']['S']

        if self._existing_mount(device):
            logger.debug('Volume %s is already mounted.', device)
            # TODO: verify mount point matches
            return

        label = volume_item['label']['S']
        index = volume_item['index']['N']
        fs_label = '%s%s' % (label, index)

        mount_point = volume.mount_point
        has_fs = self._mount_device(device, mount_point, fs_label)

        if not has_fs:
            self._breadcrumb(mount_point, 'label', label)
            self._breadcrumb(mount_point, 'index', index)

    def _mount_device(self, device, mount_point, fs_label):
        has_fs = self._has_filesystem(device)
        if not has_fs:
            self._mkfs(device, fs_label)
        else:
            self._e2fsck(device)
        self._mount(device, mount_point)
        return has_fs

    def mount_instance(self, volume):
        device = self.meta.block_device(volume.instance)
        if not device:
            return

        if self._existing_mount(device):
            logger.debug('Volume %s is already mounted.', device)
            return

        logger.debug('Attaching instance store %s to %s', device, volume.label)
        self._mount_device(device, volume.mount_point, volume.label)

    @staticmethod
    def _has_filesystem(device):
        lsblk = check_output(['/bin/lsblk', '-Pf', device], stderr=STDOUT)
        return 'FSTYPE=""' not in lsblk

    @staticmethod
    def _mkfs(device, fs_label):
        logger.debug('Volume has no filesystem, creating...')
        check_output(['mkfs', '-t', 'ext4', '-L', fs_label, device],
                     stderr=STDOUT)

    @staticmethod
    def _e2fsck(device):
        logger.debug('Volume has filesystem, verifying...')
        check_output(['/sbin/e2fsck', '-fy', device], stderr=STDOUT)
        check_output(['/sbin/resize2fs', device], stderr=STDOUT)

    @staticmethod
    def _existing_mount(device):  # pragma: no cover
        with open('/etc/mtab') as mtab_in:
            existing_mount = [mtab_line for mtab_line in mtab_in.readlines()
                              if mtab_line.startswith(device)]
        return existing_mount

    @staticmethod
    def _mount(device, mount_point):
        if not os.path.isdir(mount_point):
            os.mkdir(mount_point)
        logger.debug('Mounting %s at %s.', device, mount_point)
        check_output(['/bin/mount', device, mount_point], stderr=STDOUT)
        check_output(['/bin/chmod', '777', mount_point], stderr=STDOUT)
        logger.debug('Mounted %s at %s.', device, mount_point)

    @staticmethod
    def _breadcrumb(mount_point, fn, value):
        crumb_path = os.path.join(mount_point, '.space-%s' % fn)
        with open(crumb_path, 'w') as out:
            out.write(value)
            out.write('\n')
