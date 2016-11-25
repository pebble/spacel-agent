import logging
from collections import defaultdict

from botocore.exceptions import ClientError

logger = logging.getLogger('spacel')


class ElasticIpBinder(object):
    """
    Binds this instance to an elastic IP.
    """

    def __init__(self, clients, meta):
        self._clients = clients
        self._instance_id = meta.instance_id

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
        associated = {}
        for address in addresses:
            eip_id = address['AllocationId']
            eip_instance_id = address.get('InstanceId')
            if eip_instance_id == self._instance_id:
                logger.debug('Discovered existing attachment: %s' % eip_id)
                return True

            if 'AssociationId' not in address:
                unassociated.append(eip_id)
            elif eip_instance_id:
                associated[eip_instance_id] = eip_id

        reassociate = False
        if not unassociated and associated:
            victim = self._victim(self._instance_id, associated)
            if victim:
                victim_eip = associated[victim]
                logger.debug('Stealing %s from %s.', victim_eip, victim)
                unassociated = [victim_eip]
                reassociate = True

        logger.debug('No EIP attached, %s EIPs available.', len(unassociated))
        for eip_id in unassociated:
            try:
                associate_response = ec2.associate_address(
                    InstanceId=self._instance_id,
                    AllocationId=eip_id,
                    AllowReassociation=reassociate)
                if associate_response['AssociationId']:
                    logger.debug('Associated "%s".', eip_id)
                    return True
            except ClientError:
                pass
        logger.warn('Unable to associate EIP.')
        return False

    def _victim(self, own_id, associated):
        logger.debug('Searching for victim in %s...', associated)
        instances = self._describe_instances(own_id, associated)

        victim = self._victim_by_lc(own_id, instances)
        if victim:
            return victim
        # TODO: victim_by_age
        return None

    def _describe_instances(self, own_id, associated):
        instance_ids = [instance_id for instance_id in associated.keys()]
        instance_ids.append(own_id)

        ec2 = self._clients.ec2()
        instance_descriptions = ec2.describe_instances(InstanceIds=instance_ids)

        instances = []
        for reservation in instance_descriptions.get('Reservations', {}):
            for instance in reservation.get('Instances', ()):
                instances.append(instance)

        return instances

    @staticmethod
    def _get_lc(instance):
        for tag in instance.get('Tags', {}):
            if tag['Key'] == 'LaunchConfiguration':
                return tag['Value']
        return None

    def _victim_by_lc(self, own_id, instances):
        # Index LC membership:
        own_lc = None
        instance_lcs = defaultdict(list)
        for instance in instances:
            lc = ElasticIpBinder._get_lc(instance)
            if not lc:
                continue
            instance_id = instance['InstanceId']
            if instance_id == own_id:
                own_lc = lc
            instance_lcs[lc].append(instance_id)

        if not own_lc:
            logger.warn('Unable to determine own LC membership.')
            return None
        if len(instance_lcs) == 1:
            logger.debug('Every instance has the same LC.')
            return None

        # There are multiple LCs, sort by age:
        autoscaling = self._clients.autoscaling()
        lc_desc = autoscaling.describe_launch_configurations(
            LaunchConfigurationNames=instance_lcs.keys())
        lc_desc = lc_desc.get('LaunchConfigurations', ())
        lc_by_age = [lc['LaunchConfigurationName'] for lc in
                     sorted(lc_desc, key=lambda x: x['CreatedTime'])]

        # If there is a newer LC, don't take EIP and just wait for death:
        index_of_own = lc_by_age.index(own_lc)
        logger.debug('My LC is %s of %s.', index_of_own, len(lc_by_age))
        if index_of_own < len(lc_by_age) - 1:
            logger.debug('There is a newer LC, giving up.')
            return []

        # We're in the latest LC, chose a victim from old LC:
        for older_lc in lc_by_age[:index_of_own]:
            for potential_victim in instance_lcs[older_lc]:
                if potential_victim != own_id:
                    logger.debug('Stealing EIP from %s, old LC.',
                                 potential_victim)
                    return potential_victim
