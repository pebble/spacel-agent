import logging

from botocore.exceptions import ClientError

from spacel.agent.healthcheck import BaseHealthCheck
from spacel.aws.helpers import read_file

logger = logging.getLogger('spacel')


class ElbHealthCheck(BaseHealthCheck):
    def __init__(self, clients, meta, back_off_scale=1):
        super(ElbHealthCheck, self).__init__(back_off_scale)
        self._elb = clients.elb()
        self._instance_id = meta.instance_id

    def health(self, manifest):
        elb = manifest.elb
        if not elb:
            logger.debug('ELB not configured.')
            return True

        path = elb.get('path')
        if path:
            elb['name'] = read_file(path, None)

        elb_name = elb.get('name')
        if not elb_name:
            logger.debug('ELB name not set.')
            return True

        elb_label = '%s in %s' % (self._instance_id, elb_name)
        logger.info('Starting ELB health check for: %s', elb_label)
        in_service = self._check(elb, self._elb_in_service, elb)
        if in_service:
            logger.info('ELB health check passed: %s', elb_label)
        else:
            logger.warning('ELB health check failed: %s', elb_label)
        return in_service

    def _elb_in_service(self, elb):
        try:
            instance_health = self._elb.describe_instance_health(
                LoadBalancerName=elb['name'],
                Instances=[{'InstanceId': self._instance_id}])
            for state in instance_health.get('InstanceStates', ()):
                # This happens when the instance _was_ registered to the ELB
                # but is not any more
                if 'not currently registered' in state.get('Description', ''):
                    return self._register_instance_elb(elb)
                return state['State'].lower() == 'inservice'
        except ClientError as e:
            e_message = e.response['Error'].get('Message', '')
            if 'Could not find EC2 instance' in e_message:
                # This happens when the instance was never registered to the ELB
                return self._register_instance_elb(elb)
        return False

    def _register_instance_elb(self, elb):
        logger.info('Instance not registered with ELB, registering...')
        try:
            instances = self._elb.register_instances_with_load_balancer(
                LoadBalancerName=elb['name'],
                Instances=[{'InstanceId': self._instance_id}])
            for instance in instances.get('Instances', ()):
                if instance['InstanceId'] == self._instance_id:
                    return self._check(elb, self._elb_in_service, elb)
        except ClientError as e:
            logger.warn('Unable to register instance %s with load balancer %s',
                        self._instance_id, elb['name'])
            logger.error('%s', e)
        return False
