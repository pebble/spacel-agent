from botocore.exceptions import ClientError

from spacel.aws.eip import ElasticIpBinder
from test.aws import MockedClientTest, INSTANCE_ID

EIP_ID = 'eip-123456'
EIPS = (EIP_ID, 'eip-654321')
INSTANCE_ID2 = 'i-654321'


class TestEipBinder(MockedClientTest):
    def setUp(self):
        super(TestEipBinder, self).setUp()
        self.manifest.eips = EIPS
        self.eip = ElasticIpBinder(self.clients, self.meta)

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
                AllocationId=EIP_ID,
                AllowReassociation=False)

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

    def test_describe_instances(self):
        self.ec2.describe_instances.return_value = {
            'Reservations': [
                {'Instances': [
                    {'InstanceId': INSTANCE_ID}
                ]},
                {'Instances': [
                    {'InstanceId': INSTANCE_ID2}
                ]}
            ]
        }

        allocations = {INSTANCE_ID2: EIP_ID}
        instances = self.eip._describe_instances(INSTANCE_ID, allocations)

        instance_ids = [INSTANCE_ID2, INSTANCE_ID]
        self.ec2.describe_instances.assert_called_with(InstanceIds=instance_ids)
        self.assertEqual(2, len(instances))

    def test_get_lc(self):
        instance_data = {
            'InstanceId': INSTANCE_ID,
            'Tags': [
                {'Key': 'LaunchConfiguration', 'Value': 'test'}
            ]}

        lc = self.eip._get_lc(instance_data)
        self.assertEquals('test', lc)

    def test_get_lc_not_found(self):
        lc = self.eip._get_lc({})
        self.assertIsNone(lc)

    def test_victim_by_lc_not_found(self):
        victim = self.eip._victim_by_lc(INSTANCE_ID, [])
        self.assertIsNone(victim)

    def test_victim_by_lc_only_self(self):
        instances = [{
            'InstanceId': INSTANCE_ID,
            'Tags': [{'Key': 'LaunchConfiguration', 'Value': 'test'}]
        }]
        victim = self.eip._victim_by_lc(INSTANCE_ID, instances)
        self.assertIsNone(victim)

    def _mock_addresses(self, addresses):
        self.ec2.describe_addresses.return_value = {'Addresses': addresses}
