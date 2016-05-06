from botocore.exceptions import ClientError
import logging
import time

logger = logging.getLogger('spacel')


class ElbHealthCheck(object):
    def __init__(self, clients, meta):
        self._elb = clients.elb()
        self._instance_id = meta.instance_id

    def health(self, manifest):
        if not manifest.elb:
            logger.debug('ELB not configured.')
            return True

        for attempt in range(30):
            logger.debug('Querying ELB, attempt #%d.', attempt)
            state = self._instance_states(manifest)
            if state == 'inservice':
                logger.debug('Instance %s is healthy in %s.', self._instance_id,
                             manifest.elb)
                return True
            time.sleep(5)
        return False

    def _instance_states(self, manifest):
        try:
            instance_health = self._elb.describe_instance_health(
                    LoadBalancerName=manifest.elb,
                    Instances=[{'InstanceId': self._instance_id}])
            for state in instance_health.get('InstanceStates', ()):
                return state['State'].lower()
        except ClientError:
            pass
        return None
