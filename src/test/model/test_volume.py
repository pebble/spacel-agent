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

    def test_iops_no_type(self):
        volume = SpaceVolume(LABEL, {
            'iops': 3000
        })

        self.assertEqual(volume.type, 'gp2')
        self.assertEqual(volume.iops, None)
        self.assertEqual(volume.count, 1)
