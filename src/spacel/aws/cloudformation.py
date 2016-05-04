import logging

logger = logging.getLogger('spacel')


class CloudFormationSignaller(object):
    def __init__(self, clients, instance_id):
        self._clients = clients
        self._instance_id = instance_id

    def notify(self, manifest, status='SUCCESS'):
        if not manifest.cf_signal:
            logger.debug('No CloudFormation signals configured.')
            return

        cloudformation = self._clients.cloudformation()
        for cf_stack, cf_resource_id in manifest.cf_signal.items():
            logger.debug('Signalling %s in %s (%s).', cf_resource_id, cf_stack,
                         manifest.instance_id)
            cloudformation.signal_resource(
                    StackName=cf_stack,
                    LogicalResourceId=cf_resource_id,
                    UniqueId=self._instance_id,
                    Status=status)
