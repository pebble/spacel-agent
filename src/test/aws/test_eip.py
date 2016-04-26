import unittest
from mock import MagicMock
from botocore.exceptions import ClientError

from spacel.aws.eip import ElasticIpBinder

INSTANCE_ID = 'i-123456'
EIP_ID = 'eip-123456'
EIPS = (EIP_ID, 'eip-654321')


class TestEipBinder(unittest.TestCase):
    def setUp(self):
        self.ec2 = MagicMock()
        self.eip = ElasticIpBinder(self.ec2, INSTANCE_ID)

    def test_assign_from_has_address(self):
        self._mock_addresses([{
            'AllocationId': EIP_ID,
            'AssociationId': 'assoc-123456',
            'InstanceId': INSTANCE_ID
        }])

        got_eip = self.eip.assign_from(EIPS)
        self.assertEqual(True, got_eip)
        self.ec2.associate_address.assert_not_called()

    def test_assign_from_associate(self):
        self._mock_addresses([{
            'AllocationId': EIP_ID
        }])

        got_eip = self.eip.assign_from(EIPS)
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

        got_eip = self.eip.assign_from(EIPS)
        self.assertEqual(False, got_eip)

    def _mock_addresses(self, addresses):
        self.ec2.describe_addresses.return_value = {'Addresses': addresses}
