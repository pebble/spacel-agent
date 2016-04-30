import time

import logging

logger = logging.getLogger('spacel')


class CloudFormationSignaller(object):
    def __init__(self, clients):
        self._clients = clients

    def notify(self, manifest, status='SUCCESS'):
        if not manifest.cf_signal:
            logger.debug('No CloudFormation signals configured.')
            return

        cloudformation = self._clients.cloudformation()
        for cf_stack, cf_resource_id in manifest.cf_signal.items():
            unique_id = '%s-%d' % (manifest.instance_id, int(time.time()))
            logger.debug('Signalling %s in %s (%s).', cf_resource_id, cf_stack,
                         unique_id)
            cloudformation.signal_resource(
                    StackName=cf_stack,
                    LogicalResourceId=cf_resource_id,
                    UniqueId=unique_id,
                    Status=status)
