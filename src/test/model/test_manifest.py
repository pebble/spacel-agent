import unittest

from spacel.model.manifest import AgentManifest

INSTANCE_ID = 'i-123456'
EIP_ALLOCATION = 'eip-123456'
ELB_ID = 'elb-123456'


class TestAgentManifest(unittest.TestCase):
    def test_eips(self):
        manifest = AgentManifest({'eips': [EIP_ALLOCATION]})
        self.assertEquals(manifest.eips, [EIP_ALLOCATION])

    def test_all_files(self):
        manifest = AgentManifest({
            'files': {'foo.txt': {}},
            'systemd': {'foo.service': {}}
        })

        all_files = manifest.all_files
        self.assertEquals(2, len(all_files))
        self.assertIn('foo.txt', all_files)
        self.assertIn('foo.service', all_files)

    def test_volumes(self):
        manifest = AgentManifest({'volumes': {
            'test': {
                'size': 8
            }
        }})

        self.assertEquals(1, len(manifest.volumes))
        self.assertEquals(8, manifest.volumes['test'].size)

    def test_valid(self):
        manifest = AgentManifest({'systemd': {
            'foo.service': {}
        }})
        self.assertTrue(manifest.valid)

    def test_valid_invalid_volume(self):
        manifest = AgentManifest({'volumes': {
            'test': {
                'instance': 'meow'
            }
        }})

        self.assertFalse(manifest.valid)

    def test_valid_duplicate_volume(self):
        manifest = AgentManifest({'volumes': {
            'test': {
                'instance': 0
            },
            'test2': {
                'instance': 0
            }
        }})

        self.assertFalse(manifest.valid)

    def test_elb_string(self):
        manifest = AgentManifest({'elb': ELB_ID})

        self.assertEquals(ELB_ID, manifest.elb.get('name'))

    def test_elb_object(self):
        manifest = AgentManifest({'elb': {'name': ELB_ID}})

        self.assertEquals(ELB_ID, manifest.elb.get('name'))

    def test_elb_empty(self):
        manifest = AgentManifest({})
        self.assertIsNone(manifest.elb)
