import unittest
from StringIO import StringIO
from urllib2 import URLError

from mock import patch
from spacel.aws.meta import AwsMeta

INSTANCE_ID = 'i-123456'
AZ = 'us-west-2c'
REGION = 'us-west-2'


class TestAwsMeta(unittest.TestCase):
    @patch('spacel.aws.meta.AwsMeta._get')
    def test_constructor(self, mock_get):
        mock_get.side_effect = [
            INSTANCE_ID,
            AZ,
            '{"foo":"bar"}',
        ]
        meta = AwsMeta()

        self.assertEquals(meta.instance_id, INSTANCE_ID)
        self.assertEquals(meta.az, AZ)
        self.assertEquals(meta.region, REGION)
        self.assertEqual(meta.user_data, {'foo': 'bar'})

    @patch('spacel.aws.meta.urlopen')
    def test_get(self, mock_urlopen):
        mock_urlopen.return_value = StringIO(INSTANCE_ID)
        instance_id = AwsMeta._get('url', 'default')
        self.assertEquals(INSTANCE_ID, instance_id)

    @patch('spacel.aws.meta.urlopen')
    def test_get_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('Kaboom')
        instance_id = AwsMeta._get('url', 'default')
        self.assertEquals('default', instance_id)
