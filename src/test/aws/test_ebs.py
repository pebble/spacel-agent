from mock import ANY
from test.aws import (MockedClientTest, INSTANCE_ID, AVAILABILITY_ZONE)

from spacel.aws.ebs import VolumeBinder
from spacel.model import SpaceVolume

STACK_NAME = 'stack_name'
RESOURCE_NAME = 'resource_name'


class TestVolumeBinder(MockedClientTest):
    def setUp(self):
        super(TestVolumeBinder, self).setUp()
        self.volume = SpaceVolume('test', {
            'count': 3
        })
        self.volume_binder = VolumeBinder(self.clients, self.meta)

    def test_get_volume_assignment_create(self):
        assignment = self.volume_binder._get_volume_assignment(self.volume)

        self.assertEquals(INSTANCE_ID, assignment['assignment']['S'])
        self.assertEquals(AVAILABILITY_ZONE, assignment['az']['S'])
        self.assertEquals('0', assignment['volume_index']['N'])

        self.dynamodb.put_item.assert_called_with(
                TableName=ANY,
                Item=ANY,
                ConditionExpression=ANY)
        self.dynamodb.update_item.assert_not_called()

    def test_get_volume_assignment_existing(self):
        existing_assignment = {'volume_index': {'N': '1'},
                               'assignment': {'S': INSTANCE_ID}}
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                'volumes': [existing_assignment]
            }
        }

        assignment = self.volume_binder._get_volume_assignment(self.volume)
        self.assertEquals('1', assignment['volume_index']['N'])

        self.dynamodb.put_item.assert_not_called()
        self.dynamodb.update_item.assert_not_called()

    def test_get_volume_assignment_dead_instance(self):
        self._mock_volume_records()
        self.ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {
                        'InstanceId': 'i-111111',
                        'State': {'Name': 'Running'}
                    },
                    {
                        'InstanceId': 'i-222222',
                        'State': {'Name': 'Pending'}
                    },
                    {
                        'InstanceId': 'i-333333',
                        'State': {'Name': 'Terminated'}
                    }

                ]
            }]
        }

        assignment = self.volume_binder._get_volume_assignment(self.volume)
        # Assignment takes over the terminated instance:
        self.assertEquals('2', assignment['volume_index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def test_get_volume_assignment_missing_instance(self):
        self._mock_volume_records()
        self.ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [
                    {
                        'InstanceId': 'i-111111',
                        'State': {'Name': 'Running'}
                    },
                    {
                        'InstanceId': 'i-222222',
                        'State': {'Name': 'Pending'}
                    }
                ]
            }]
        }

        assignment = self.volume_binder._get_volume_assignment(self.volume)
        # Assignment takes over the terminated instance:
        self.assertEquals('2', assignment['volume_index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def test_get_volume_assignment_prefer_own_az(self):
        self._mock_volume_records()
        self.ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': 'i-111111',
                    'State': {'Name': 'Terminated'}
                }, {
                    'InstanceId': 'i-222222',
                    'State': {'Name': 'Terminated'}
                }, {
                    'InstanceId': 'i-333333',
                    'State': {'Name': 'Terminated'}
                }]
            }]
        }

        assignment = self.volume_binder._get_volume_assignment(self.volume)
        # Assignment takes over the terminated instance in our AZ:
        self.assertEquals('1', assignment['volume_index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def _mock_volume_records(self):
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                'volumes': [{'volume_index': {'N': '0'},
                             'assignment': {'S': 'i-111111'},
                             'az': 'us-west-2a'},
                            {'volume_index': {'N': '1'},
                             'assignment': {'S': 'i-222222'},
                             'az': 'us-west-2b'},
                            {'volume_index': {'N': '2'},
                             'assignment': {'S': 'i-333333'},
                             'az': 'us-west-2c'}]
            }
        }
