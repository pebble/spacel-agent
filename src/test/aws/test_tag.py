from spacel.aws.tag import TagWriter
from test.aws import MockedClientTest, INSTANCE_ID

TAG_KEY = 'key'
TAG_VALUE = 'value'


class TestTagWriter(MockedClientTest):
    def setUp(self):
        super(TestTagWriter, self).setUp()
        self.tag_writer = TagWriter(self.clients, self.meta)

        self.manifest.tags = {TAG_KEY: TAG_VALUE}

    def test_update(self):
        self.tag_writer.update(self.manifest)

        self.ec2.create_tags.assert_called_once_with(
            Resources=[INSTANCE_ID],
            Tags=[{'Key': TAG_KEY, 'Value': TAG_VALUE}]
        )

    def test_update_empty(self):
        self.manifest.tags = ()

        self.tag_writer.update(self.manifest)

        self.ec2.create_tags.assert_not_called()
