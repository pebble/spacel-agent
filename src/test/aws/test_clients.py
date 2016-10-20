import unittest

from mock import patch
from spacel.aws.clients import ClientCache

REGION = 'us-east-1'


class TestClientCache(unittest.TestCase):
    def setUp(self):
        self.clients = ClientCache(REGION)

    @patch('spacel.aws.clients.boto3')
    def test_autoscaling(self, mock_boto3):
        self.clients.autoscaling()
        mock_boto3.client.assert_called_once_with('autoscaling', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_cloudformation(self, mock_boto3):
        self.clients.cloudformation()
        mock_boto3.client.assert_called_once_with('cloudformation', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_dynamodb(self, mock_boto3):
        self.clients.dynamodb()
        mock_boto3.client.assert_called_once_with('dynamodb', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2(self, mock_boto3):
        self.clients.ec2()
        mock_boto3.client.assert_called_once_with('ec2', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_ec2_cached(self, mock_boto3):
        self.clients.ec2()
        self.clients.ec2()
        self.assertEqual(1, mock_boto3.client.call_count)

    @patch('spacel.aws.clients.boto3')
    def test_elb(self, mock_boto3):
        self.clients.elb()
        mock_boto3.client.assert_called_once_with('elb', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_elasticache(self, mock_boto3):
        self.clients.elasticache()
        mock_boto3.client.assert_called_once_with('elasticache', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_kms(self, mock_boto3):
        self.clients.kms(REGION)
        mock_boto3.client.assert_called_once_with('kms', REGION)

    @patch('spacel.aws.clients.boto3')
    def test_rds(self, mock_boto3):
        self.clients.rds(REGION)
        mock_boto3.client.assert_called_once_with('rds', REGION)
