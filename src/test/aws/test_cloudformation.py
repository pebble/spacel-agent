from botocore.exceptions import ClientError
from mock import patch
from spacel.aws import CloudFormationSignaller
from test.aws import MockedClientTest, INSTANCE_ID

STACK_NAME = 'stack_name'
RESOURCE_NAME = 'resource_name'


class TestCloudFormationSignaller(MockedClientTest):
    def setUp(self):
        super(TestCloudFormationSignaller, self).setUp()
        self.signaller = CloudFormationSignaller(self.clients, INSTANCE_ID)

        self.manifest.cf_signal = {STACK_NAME: RESOURCE_NAME}

    def test_notify_not_enabled(self):
        self.manifest.cf_signal = {}
        self.signaller.notify(self.manifest)
        self.cloudformation.signal_resource.assert_not_called()

    def test_notify(self):
        self.signaller.notify(self.manifest)
        self.cloudformation.signal_resource.assert_called_with(
                StackName=STACK_NAME,
                LogicalResourceId=RESOURCE_NAME,
                UniqueId=INSTANCE_ID,
                Status='SUCCESS')

    def test_notify_exception_caught(self):
        client_error = ClientError({'Error': {'Code': 'ValidationError'}}, '')
        self.cloudformation.signal_resource.side_effect = client_error
        self.signaller.notify(self.manifest)
        self.cloudformation.signal_resource.assert_called_with(
                StackName=STACK_NAME,
                LogicalResourceId=RESOURCE_NAME,
                UniqueId=INSTANCE_ID,
                Status='SUCCESS')

    def test_notify_exception(self):
        client_error = ClientError({'Error': {'Code': 'Kaboom'}}, '')
        self.cloudformation.signal_resource.side_effect = client_error
        self.assertRaises(ClientError, self.signaller.notify, self.manifest)
        self.cloudformation.signal_resource.assert_called_with(
                StackName=STACK_NAME,
                LogicalResourceId=RESOURCE_NAME,
                UniqueId=INSTANCE_ID,
                Status='SUCCESS')

    @patch('spacel.aws.cloudformation.read_file')
    def test_notify_path(self, mock_read_file):
        mock_read_file.side_effect = [STACK_NAME, RESOURCE_NAME]
        self.manifest.cf_signal = {
            'path:/home/stack': 'path:/home/resource_id'
        }
        self.signaller.notify(self.manifest)
        self.cloudformation.signal_resource.assert_called_with(
                StackName=STACK_NAME,
                LogicalResourceId=RESOURCE_NAME,
                UniqueId=INSTANCE_ID,
                Status='SUCCESS')

    @patch('spacel.aws.cloudformation.read_file')
    def test_notify_path_not_found(self, mock_read_file):
        mock_read_file.side_effect = [STACK_NAME, None]
        self.manifest.cf_signal = {
            'path:/home/stack': 'path:/home/resource_id'
        }
        self.signaller.notify(self.manifest)
        self.cloudformation.signal_resource.assert_not_called()
