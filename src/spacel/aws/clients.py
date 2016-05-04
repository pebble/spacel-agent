import boto3
import logging

logger = logging.getLogger('spacel')


class ClientCache(object):
    """
    Lazy instantiation container for AWS clients.
    """

    def __init__(self, region):
        self._clients = {}
        self.region = region

    def autoscaling(self):
        """
        Get AutoScaling client.
        :return: AutoScaling client.
        """
        return self._client('autoscaling')

    def cloudformation(self):
        """
        Get CloudFormation client.
        :return: CloudFormation client.
        """
        return self._client('cloudformation')

    def dynamodb(self):
        """
        Get DynamoDb client.
        :return: DynamoDb client.
        """
        return self._client('dynamodb')

    def ec2(self):
        """
        :return: EC2 client.
        """
        return self._client('ec2')

    def _client(self, client_type):
        cached = self._clients.get(client_type)
        if cached:
            return cached
        logger.debug('Connecting to %s in %s.', client_type, self.region)
        client = boto3.client(client_type, self.region)
        self._clients[client_type] = client
        return client
