from mock import ANY
from spacel.model import SpaceVolume
from spacel.volumes.db import VolumeDb
from test.aws import MockedClientTest, INSTANCE_ID, AVAILABILITY_ZONE
from test.volumes import LABEL, VOLUME_INDEX

TABLE_NAME = 'unittest-volumes'


class TestVolumeDb(MockedClientTest):
    def setUp(self):
        super(TestVolumeDb, self).setUp()
        self.volume = SpaceVolume(LABEL, {
            'count': 3
        })
        self.volume_db = VolumeDb(self.clients, self.meta)

    def test_get_volume_items(self):
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                TABLE_NAME: [{
                    'label': {'S': LABEL},
                    'index': {'N': VOLUME_INDEX}
                }]
            }
        }
        volume_items = self.volume_db._get_volume_items(self.volume)
        self.assertEquals(1, len(volume_items))

    def test_get_volume_items_empty(self):
        volume_items = self.volume_db._get_volume_items(self.volume)
        self.assertEquals(0, len(volume_items))

    def test_get_assignment_create(self):
        assignment = self.volume_db.get_assignment(self.volume)

        self.assertEquals(INSTANCE_ID, assignment['assignment']['S'])
        self.assertEquals(AVAILABILITY_ZONE, assignment['az']['S'])
        self.assertEquals(VOLUME_INDEX, assignment['index']['N'])

        self.dynamodb.put_item.assert_called_with(
                TableName=TABLE_NAME,
                Item={
                    'label': {'S': LABEL},
                    'index': {'N': VOLUME_INDEX},
                    'az': {'S': AVAILABILITY_ZONE},
                    'assignment': {'S': INSTANCE_ID}
                },
                ConditionExpression=ANY)
        self.dynamodb.update_item.assert_not_called()

    def test_get_assignment_existing(self):
        existing_assignment = {'index': {'N': '1'},
                               'assignment': {'S': INSTANCE_ID}}
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                TABLE_NAME: [existing_assignment]
            }
        }

        assignment = self.volume_db.get_assignment(self.volume)
        self.assertEquals('1', assignment['index']['N'])

        self.dynamodb.put_item.assert_not_called()
        self.dynamodb.update_item.assert_not_called()

    def test_get_assignment_dead_instance(self):
        self._mock_volume_records()
        self._mock_instances('Running', 'Pending', 'Terminated')

        assignment = self.volume_db.get_assignment(self.volume)
        # Assignment takes over the terminated instance:
        self.assertEquals('2', assignment['index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def test_get_assignment_missing_instance(self):
        self._mock_volume_records()
        self._mock_instances('Running', 'Pending')

        assignment = self.volume_db.get_assignment(self.volume)
        # Assignment takes over the missing instance:
        self.assertEquals('2', assignment['index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def test_get_assignment_prefer_own_az(self):
        self._mock_volume_records()
        self._mock_instances('Terminated', 'Terminated', 'Terminated')

        assignment = self.volume_db.get_assignment(self.volume)
        # Assignment takes over the terminated instance in our AZ:
        self.assertEquals('1', assignment['index']['N'])
        self.dynamodb.update_item.assert_called_with(
                TableName=ANY,
                Key=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY,
                ConditionExpression=ANY
        )

    def test_get_assignment_none_available(self):
        self._mock_volume_records()
        self._mock_instances('Running', 'Running', 'Running')

        assignment = self.volume_db.get_assignment(self.volume)
        self.assertIsNone(assignment)

    def test_volume_key(self):
        volume_key = self.volume_db._volume_key(LABEL, VOLUME_INDEX)
        self.assertEquals(2, len(volume_key))
        self.assertEquals(LABEL, volume_key['label']['S'])
        self.assertEquals(VOLUME_INDEX, volume_key['index']['N'])

    def test_save_noop(self):
        self.volume_db.save({
            'label': {'S': LABEL},
            'index': {'N': VOLUME_INDEX}
        })
        self.dynamodb.update_item.assert_not_called()

    def test_save(self):
        self.volume_db.save({
            'label': {'S': LABEL},
            'index': {'N': VOLUME_INDEX},
            'volume_id': {'S': 'vol-123456'}
        })
        self.dynamodb.update_item.assert_called_with(
                TableName=TABLE_NAME,
                Key=ANY,
                ConditionExpression=ANY,
                UpdateExpression=ANY,
                ExpressionAttributeValues=ANY)

    def _mock_instances(self, *args):
        i = 1
        instances = []
        for arg in args:
            instances.append({'InstanceId': 'i-%s' % (str(i) * 6),
                              'State': {'Name': arg}})
            i += 1
        self.ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': instances
            }]
        }

    def _mock_volume_records(self):
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                TABLE_NAME: [{'index': {'N': '0'},
                              'assignment': {'S': 'i-111111'},
                              'az': 'us-west-2a'},
                             {'index': {'N': '1'},
                              'assignment': {'S': 'i-222222'},
                              'az': 'us-west-2b'},
                             {'index': {'N': '2'},
                              'assignment': {'S': 'i-333333'},
                              'az': 'us-west-2c'}]
            }
        }
