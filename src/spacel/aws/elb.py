from botocore.exceptions import ClientError
import logging

from spacel.agent.healthcheck import BaseHealthCheck

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

        return self._check(elb, self._elb_in_service, elb)

    def _elb_in_service(self, elb):
        try:
            instance_health = self._elb.describe_instance_health(
                LoadBalancerName=elb['name'],
                Instances=[{'InstanceId': self._instance_id}])
            for state in instance_health.get('InstanceStates', ()):
                return state['State'].lower() == 'inservice'
        except ClientError:
            pass
        return False
