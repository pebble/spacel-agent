import unittest

from mock import MagicMock
from spacel.model import AgentManifest

INSTANCE_ID = 'i-123456'


class MockedClientTest(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock()
        self.ec2 = MagicMock()
        self.clients.ec2.return_value = self.ec2
        self.cloudformation = MagicMock()
        self.clients.cloudformation.return_value = self.cloudformation
        self.manifest = AgentManifest(INSTANCE_ID)
