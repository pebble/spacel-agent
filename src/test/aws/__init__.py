import unittest

from mock import MagicMock
from spacel.model import AgentManifest
from spacel.aws import AwsMeta, ClientCache

INSTANCE_ID = 'i-123456'
AVAILABILITY_ZONE = 'us-west-2b'


class MockedClientTest(unittest.TestCase):
    def setUp(self):
        self.autoscaling = MagicMock()
        self.cloudformation = MagicMock()
        self.dynamodb = MagicMock()
        self.ec2 = MagicMock()
        self.elb = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.clients.autoscaling.return_value = self.autoscaling
        self.clients.cloudformation.return_value = self.cloudformation
        self.clients.dynamodb.return_value = self.dynamodb
        self.clients.ec2.return_value = self.ec2
        self.clients.elb.return_value = self.elb
        self.meta = MagicMock(spec=AwsMeta)
        self.meta.instance_id = INSTANCE_ID
        self.meta.az = AVAILABILITY_ZONE
        self.meta.region = AVAILABILITY_ZONE[:-1]
        self.meta.orbit = 'unittest'
        self.manifest = AgentManifest()
