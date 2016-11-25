from spacel.aws.tag import InstanceTags
from test.aws import MockedClientTest, INSTANCE_ID

TAG_KEY = 'key'
TAG_VALUE = 'value'

TAGS_EC2 = [{'Key': TAG_KEY, 'Value': TAG_VALUE}]
TAGS_PYTHON = {TAG_KEY: TAG_VALUE}


class TestInstanceTags(MockedClientTest):
    def setUp(self):
        super(TestInstanceTags, self).setUp()
        self.instance_tags = InstanceTags(self.clients, self.meta)
        self.manifest.tags = TAGS_PYTHON

    def test_get(self):
        self.ec2.describe_instances.return_value = {
            'Reservations': [{
                'Instances': [{
                    'InstanceId': INSTANCE_ID,
                    'Tags': TAGS_EC2
                }]
            }]
        }

        tags = self.instance_tags.get()
        self.assertEquals(TAGS_PYTHON, tags)

    def test_get_missing(self):
        tags = self.instance_tags.get()
        self.assertEquals({}, tags)

    def test_update(self):
        self.instance_tags.update(self.manifest)

        self.ec2.create_tags.assert_called_once_with(
            Resources=[INSTANCE_ID],
            Tags=TAGS_EC2
        )

    def test_update_empty(self):
        self.manifest.tags = ()

        self.instance_tags.update(self.manifest)

        self.ec2.create_tags.assert_not_called()
