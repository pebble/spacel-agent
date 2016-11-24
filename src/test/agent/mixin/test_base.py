import shutil
import tempfile
import unittest

from spacel.agent.mixin.base import BaseMixinWriter


class TestBaseMixinWriter(unittest.TestCase):
    def setUp(self):
        self.systemd = tempfile.mkdtemp()
        self.mixin_writer = BaseMixinWriter(None, systemd_path=self.systemd)

    def tearDown(self):
        shutil.rmtree(self.systemd)

    def test_write_mixin(self):
        self.mixin_writer._write_mixin(
            'test.service', '10-test', {
                'FOO': 'bar'
            })

        with open(self.systemd + '/test.service.d/10-test.conf') as mixin_in:
            mixin = [l.strip() for l in mixin_in.readlines()]
        self.assertEquals('[Service]', mixin[0])
        self.assertIn('Environment=', mixin[1])
