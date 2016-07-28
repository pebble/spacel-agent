from botocore.exceptions import ClientError
from spacel.aws.elb import ElbHealthCheck
from test.aws import MockedClientTest, INSTANCE_ID

ELB_NAME = 'elb-123456'
INSTANCE_IN_SERVICE = {'InstanceStates': [{'State': 'InService'}]}


class TestElbHealthCheck(MockedClientTest):
    def setUp(self):
        super(TestElbHealthCheck, self).setUp()
        self.elb_health = ElbHealthCheck(self.clients, self.meta, 0.000001)

        self.manifest.elb = ELB_NAME

    def test_health_no_elb(self):
        self.manifest.elb = None

        health = self.elb_health.health(self.manifest)

        self.assertTrue(health)
        self.elb.describe_instance_health.assert_not_called()

    def test_health_timeout(self):
        self.manifest.elb_time = 0.01

        health = self.elb_health.health(self.manifest)

        self.assertFalse(health)
        self.assertTrue(self.elb.describe_instance_health.call_count > 1)

    def test_health_healthy(self):
        self.elb.describe_instance_health.return_value = INSTANCE_IN_SERVICE

        health = self.elb_health.health(self.manifest)

        self.assertTrue(health)
        self.elb.describe_instance_health.assert_called_once_with(
            LoadBalancerName=ELB_NAME,
            Instances=[{'InstanceId': INSTANCE_ID}]
        )

    def test_health_retry(self):
        describe_exception = ClientError({'Error': {'Message': 'Kaboom'}},
                                         'DescribeInstanceHealth')
        self.elb.describe_instance_health.side_effect = [
            describe_exception,
            INSTANCE_IN_SERVICE
        ]

        health = self.elb_health.health(self.manifest)
        self.assertTrue(health)
