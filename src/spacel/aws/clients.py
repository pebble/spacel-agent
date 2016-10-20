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

    def elb(self):
        """
        :return: ELB client.
        """
        return self._client('elb')

    def elasticache(self):
        """
        :return: ElastiCache client.
        """
        return self._client('elasticache')

    def kms(self, region):
        """
        Get KMS client.
        :param region: Region.
        :return:  KMS Client.
        """
        return self._client('kms', region)

    def rds(self, region):
        """
        Get RDS client.
        :param region:  Region.
        :return:  RDS client.
        """
        return self._client('rds', region)

    def _client(self, client_type, region=None):
        cached = self._clients.get(client_type)
        if cached:
            return cached
        region = region or self.region
        logger.debug('Connecting to %s in %s.', client_type, region)
        client = boto3.client(client_type, region)
        self._clients[client_type] = client
        return client
