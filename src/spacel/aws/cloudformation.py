import logging
from botocore.exceptions import ClientError
from spacel.aws.helpers import read_file

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
            if cf_stack.startswith('path:/'):
                cf_stack = cf_stack.replace('path:', '').strip()
                cf_stack = read_file(cf_stack, None)
            if cf_resource_id.startswith('path:/'):
                cf_resource_id = cf_resource_id.replace('path:', '').strip()
                cf_resource_id = read_file(cf_resource_id, None)
            if cf_stack is None or cf_resource_id is None:
                logger.debug('CFN: Stack/Resource ID not found!')
                return

            logger.debug('Signalling %s in %s (%s).', cf_resource_id, cf_stack,
                         self._instance_id)
            try:
                cloudformation.signal_resource(
                        StackName=cf_stack,
                        LogicalResourceId=cf_resource_id,
                        UniqueId=self._instance_id,
                        Status=status)
            except ClientError as e:
                logger.debug('Could not signal CloudFormation!')
                if e.response['Error']['Code'] != 'ValidationError':
                    raise e
