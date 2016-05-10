from mock import patch
import os
import shutil
import tempfile
import unittest

from spacel.volumes.fs import DeviceMount

DEVICE = '/dev/xvdb'


class TestDeviceMount(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.device_mount = DeviceMount()

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
        self.device_mount._mkfs(DEVICE)

    @patch('spacel.volumes.fs.check_output')
    def test_e2fsck(self, _):
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
