import logging
from botocore.exceptions import ClientError

logger = logging.getLogger('spacel')


class ElasticIpBinder(object):
    """
    Binds this instance to an elastic IP.
    """

    def __init__(self, clients):
        self._clients = clients

    def assign_from(self, manifest):
        """
        Assign EIP if configured.
        :param manifest: Manifest.
        :return: True if EIP was assigned, false otherwise.
        """
        if not manifest.eips:
            logger.debug('Manifest does not configure EIP.')
            return True

        ec2 = self._clients.ec2()
        addresses = ec2.describe_addresses(Filters=[{
            'Name': 'allocation-id',
            'Values': manifest.eips
        }])['Addresses']

        unassociated = []
        for address in addresses:
            eip_id = address['AllocationId']
            if address.get('InstanceId') == manifest.instance_id:
                logger.debug('Discovered existing attachment: %s' % eip_id)
                return True

            if 'AssociationId' not in address:
                unassociated.append(eip_id)

        logger.debug('No EIP attached, %s EIPs available.', len(unassociated))
        for eip_id in unassociated:
            try:
                associate_response = ec2.associate_address(
                        InstanceId=manifest.instance_id,
                        AllocationId=eip_id)
                if associate_response['AssociationId']:
                    logger.debug('Associated "%s".', eip_id)
                    return True
            except ClientError:
                pass
        logger.warn('Unable to associate EIP.')
        return False
