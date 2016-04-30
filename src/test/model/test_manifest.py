import unittest

from spacel.model.manifest import AgentManifest

INSTANCE_ID = 'i-123456'
EIP_ALLOCATION = 'eip-123456'


class TestAgentManifest(unittest.TestCase):
    def test_eips(self):
        manifest = AgentManifest(INSTANCE_ID, {'eips': [EIP_ALLOCATION]})
        self.assertEquals(manifest.eips, [EIP_ALLOCATION])

    def test_all_files(self):
        manifest = AgentManifest(INSTANCE_ID, {
            'files': {'foo.txt': {}},
            'systemd': {'foo.service': {}}
        })

        all_files = manifest.all_files
        self.assertEquals(2, len(all_files))
        self.assertIn('foo.txt', all_files)
        self.assertIn('foo.service', all_files)
