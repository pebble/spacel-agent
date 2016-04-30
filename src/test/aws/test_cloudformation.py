from mock import ANY

from spacel.aws import CloudFormationSignaller
from test.aws import MockedClientTest

STACK_NAME = 'stack_name'
RESOURCE_NAME = 'resource_name'


class TestCloudFormationSignaller(MockedClientTest):
    def setUp(self):
        super(TestCloudFormationSignaller, self).setUp()
        self.signaller = CloudFormationSignaller(self.clients)

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
                UniqueId=ANY,
                Status='SUCCESS')
