import unittest

from mock import patch
from spacel.aws.clients import ClientCache

REGION = 'us-east-1'


class TestClientCache(unittest.TestCase):
    def setUp(self):
        self.clients = ClientCache()

    @patch('spacel.aws.clients.boto3')
    def test_ec2(self, mock_boto3):
        self.clients.ec2(REGION)
        mock_boto3.client.assert_called_once_with('ec2', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2_cached(self, mock_boto3):
        self.clients._ec2[REGION] = True
        self.clients.ec2(REGION)
        mock_boto3.client.assert_not_called()
