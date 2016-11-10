import logging

import boto3

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
        return self.client('autoscaling')

    def cloudformation(self):
        """
        Get CloudFormation client.
        :return: CloudFormation client.
        """
        return self.client('cloudformation')

    def dynamodb(self):
        """
        Get DynamoDb client.
        :return: DynamoDb client.
        """
        return self.client('dynamodb')

    def ec2(self):
        """
        Get EC2 client.
        :return: EC2 client.
        """
        return self.client('ec2')

    def elb(self):
        """
        Get ELB client.
        :return: ELB client.
        """
        return self.client('elb')

    def elasticache(self):
        """
        Get ElastiCache client.
        :return: ElastiCache client.
        """
        return self.client('elasticache')

    def kms(self, region):
        """
        Get KMS client.
        :param region: Region.
        :return:  KMS Client.
        """
        return self.client('kms', region)

    def rds(self, region):
        """
        Get RDS client.
        :param region:  Region.
        :return:  RDS client.
        """
        return self.client('rds', region)

    def logs(self):
        """
        Get CloudWatchLogs client.
        :return: CloudWatchLogs client.
        """
        return self.client('logs')

    def client(self, service_name, region=None):
        cached = self._clients.get(service_name)
        if cached:
            return cached
        region = region or self.region
        logger.debug('Connecting to %s in %s.', service_name, region)
        client = boto3.client(service_name, region)
        self._clients[service_name] = client
        return client
