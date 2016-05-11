import unittest

from spacel.model.volume import SpaceVolume

LABEL = 'test'


class TestSpaceVolume(unittest.TestCase):
    def test_iops(self):
        volume = SpaceVolume(LABEL, {
            'count': 3,
            'type': 'io1',
            'iops': 3000
        })

        self.assertEqual(volume.type, 'io1')
        self.assertEqual(volume.iops, 3000)
        self.assertEqual(volume.count, 3)
        self.assertTrue(volume.valid, True)

    def test_iops_no_type(self):
        volume = SpaceVolume(LABEL, {
            'iops': 3000
        })

        self.assertEqual(volume.type, 'gp2')
        self.assertEqual(volume.iops, None)
        self.assertEqual(volume.count, 1)
        self.assertFalse(volume.valid)

    def test_instance_store(self):
        volume = SpaceVolume(LABEL, {
            'instance': 'meow'
        })
        self.assertIsNone(volume.instance)
        self.assertFalse(volume.valid)
