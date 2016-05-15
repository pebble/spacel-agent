from mock import patch, MagicMock
import os
import shutil
import tempfile
from test.aws import MockedClientTest
from test.volumes import LABEL, DEVICE, VOLUME_INDEX
from subprocess import CalledProcessError
from spacel.model import SpaceVolume
from spacel.volumes.fs import DeviceMount

MOUNT_POINT = '/mnt/%s' % LABEL


class TestDeviceMount(MockedClientTest):
    def setUp(self):
        super(TestDeviceMount, self).setUp()
        self.home = tempfile.mkdtemp()
        self.device_mount = DeviceMount(self.meta)
        self.volume = SpaceVolume(LABEL, {})

        self.volume_item = {
            'device': {'S': DEVICE},
            'label': {'S': LABEL},
            'index': {'N': VOLUME_INDEX}
        }

    def tearDown(self):
        if os.path.isdir(self.home):
            shutil.rmtree(self.home)

    @patch('spacel.volumes.fs.check_output')
    def test_has_filesystem(self, _):
        self.assertEquals(True, self.device_mount._has_filesystem('DEVICE'))

    @patch('spacel.volumes.fs.check_output')
    def test_has_filesystem_empty(self, mock_lsblk):
        mock_lsblk.return_value = 'FSTYPE=""'
        self.assertEquals(False, self.device_mount._has_filesystem('DEVICE'))

    @patch('spacel.volumes.fs.check_output')
    def test_mkfs(self, _):
        self.device_mount._mkfs(DEVICE, LABEL)

    @patch('spacel.volumes.fs.check_output')
    def test_e2fsck(self, _):
        self.device_mount._e2fsck(DEVICE)

    @patch('spacel.volumes.fs.check_output')
    def test_e2fsck_error(self, mock_call):
        mock_call.side_effect = CalledProcessError(-1, '')
        self.device_mount._e2fsck(DEVICE)

    @patch('spacel.volumes.fs.check_output')
    def test_mount(self, _):
        self.device_mount._mount(DEVICE, self.home)

    @patch('spacel.volumes.fs.check_output')
    def test_mount_create(self, _):
        shutil.rmtree(self.home)
        self.device_mount._mount(DEVICE, self.home)

    def test_breadcrumb(self):
        self.device_mount._breadcrumb(self.home, 'foo', 'bar')
        files = os.listdir(self.home)
        self.assertEquals(1, len(files))
        self.assertIn('.space-foo', files)

    def test_mount_instance_not_found(self):
        self.device_mount._mount_device = MagicMock()
        self.meta.block_device.return_value = None

        self.device_mount.mount_instance(self.volume)

        self.device_mount._mount_device.assert_not_called()

    def test_mount_instance_mounted(self):
        self.device_mount._mount_device = MagicMock()
        self.device_mount._existing_mount = MagicMock(return_value=True)

        self.device_mount.mount_instance(self.volume)

        self.device_mount._mount_device.assert_not_called()

    def test_mount_instance(self):
        self.device_mount._mount_device = MagicMock()
        self.meta.block_device.return_value = DEVICE
        self.device_mount._existing_mount = MagicMock(return_value=False)

        self.device_mount.mount_instance(self.volume)

        self.device_mount._mount_device.assert_called_with(DEVICE,
                                                           MOUNT_POINT,
                                                           LABEL)

    def test_mount_device_mkfs(self):
        self.device_mount._has_filesystem = MagicMock(return_value=False)
        self.device_mount._mkfs = MagicMock()
        self.device_mount._e2fsck = MagicMock()
        self.device_mount._mount = MagicMock()

        self.device_mount._mount_device(DEVICE, MOUNT_POINT, LABEL)

        self.device_mount._mkfs.assert_called_with(DEVICE, LABEL)
        self.device_mount._e2fsck.assert_not_called()

    def test_mount_device_e2fsck(self):
        self.device_mount._has_filesystem = MagicMock(return_value=True)
        self.device_mount._mkfs = MagicMock()
        self.device_mount._e2fsck = MagicMock()
        self.device_mount._mount = MagicMock()

        self.device_mount._mount_device(DEVICE, MOUNT_POINT, LABEL)

        self.device_mount._mkfs.assert_not_called()
        self.device_mount._e2fsck.assert_called_with(DEVICE)

    def test_mount_exists(self):
        self.device_mount._existing_mount = MagicMock(return_value=True)
        self.device_mount._mount_device = MagicMock()

        self.device_mount.mount(self.volume, self.volume_item)

        self.device_mount._mount_device.assert_not_called()

    def test_mount(self):
        self.device_mount._existing_mount = MagicMock(return_value=False)
        self.device_mount._mount_device = MagicMock(return_value=False)
        self.device_mount._breadcrumb = MagicMock()

        self.device_mount.mount(self.volume, self.volume_item)

        fs_label = '%s%s' % (LABEL, VOLUME_INDEX)
        self.device_mount._mount_device.assert_called_with(DEVICE, MOUNT_POINT,
                                                           fs_label)
