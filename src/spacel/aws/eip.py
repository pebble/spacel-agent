import logging
from botocore.exceptions import ClientError

logger = logging.getLogger('spacel')


class ElasticIpBinder(object):
    """
    Binds this instance to an elastic IP.
    """

    def __init__(self, ec2, instance_id):
        self._ec2 = ec2
        self._id = instance_id

    def assign_from(self, eips):
        """
        Assign EIP if available.
        :param eips: EIP candidate list.
        :return: True if EIP was assigned, false otherwise.
        """
        addresses = self._ec2.describe_addresses(Filters=[{
            'Name': 'allocation-id',
            'Values': eips
        }])['Addresses']

        unassociated = []
        for address in addresses:
            eip_id = address['AllocationId']
            if address.get('InstanceId') == self._id:
                logger.debug('Discovered existing attachment: %s' % eip_id)
                return True

            if 'AssociationId' not in address:
                unassociated.append(eip_id)

        logger.debug('No EIP attached, %s EIPs available.', len(unassociated))
        for eip_id in unassociated:
            try:
                associate_response = self._ec2.associate_address(
                        InstanceId=self._id,
                        AllocationId=eip_id)
                if associate_response['AssociationId']:
                    return True
            except ClientError:
                pass
        logger.warn('Unable to associate EIP.')
        return False
