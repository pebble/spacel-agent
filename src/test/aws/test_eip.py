from botocore.exceptions import ClientError

from spacel.aws.eip import ElasticIpBinder
from spacel.model import AgentManifest
from test.aws import MockedClientTest, INSTANCE_ID

EIP_ID = 'eip-123456'
EIPS = (EIP_ID, 'eip-654321')


class TestEipBinder(MockedClientTest):
    def setUp(self):
        super(TestEipBinder, self).setUp()
        self.manifest.eips = EIPS
        self.eip = ElasticIpBinder(self.clients)

    def test_assign_from_has_address(self):
        self._mock_addresses([{
            'AllocationId': EIP_ID,
            'AssociationId': 'assoc-123456',
            'InstanceId': INSTANCE_ID
        }])

        got_eip = self.eip.assign_from(self.manifest)
        self.assertEqual(True, got_eip)
        self.ec2.associate_address.assert_not_called()

    def test_assign_from_associate(self):
        self._mock_addresses([{
            'AllocationId': EIP_ID
        }])

        got_eip = self.eip.assign_from(self.manifest)
        self.assertEqual(True, got_eip)
        self.ec2.associate_address.assert_called_with(
                InstanceId=INSTANCE_ID,
                AllocationId=EIP_ID)

    def test_assign_from_associate_failed(self):
        self._mock_addresses([{
            'AllocationId': EIP_ID
        }])
        self.ec2.associate_address.side_effect = ClientError({'Error': {}},
                                                             'AssociateAddress')

        got_eip = self.eip.assign_from(self.manifest)
        self.assertEqual(False, got_eip)

    def test_assign_not_configured(self):
        self.manifest.eips = ()
        got_eip = self.eip.assign_from(self.manifest)
        self.assertEquals(True, got_eip)

    def _mock_addresses(self, addresses):
        self.ec2.describe_addresses.return_value = {'Addresses': addresses}
