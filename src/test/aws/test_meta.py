import unittest
from StringIO import StringIO
from urllib2 import URLError

from mock import patch, MagicMock
from spacel.aws.meta import AwsMeta

INSTANCE_ID = 'i-123456'
AZ = 'us-west-2c'
REGION = 'us-west-2'
JSON = '{"foo":"bar"}'


class TestAwsMeta(unittest.TestCase):
    @patch('spacel.aws.meta.AwsMeta._get')
    def setUp(self, mock_get):
        mock_get.side_effect = [
            INSTANCE_ID,
            AZ,
            JSON,
        ]
        self.meta = AwsMeta()

    def test_constructor(self):
        self.assertEquals(self.meta.instance_id, INSTANCE_ID)
        self.assertEquals(self.meta.az, AZ)
        self.assertEquals(self.meta.region, REGION)
        self.assertEqual(self.meta.user_data, {'foo': 'bar'})

    def test_parse_user_data_json(self):
        result = self.meta._parse_user_data(JSON)
        self.assertEqual(result, {'foo': 'bar'})

    def test_parse_user_data_cloud_config(self):
        self.meta._read_file = MagicMock()
        self.meta._read_file.return_value = JSON
        cloudconfig = """#cloud-config

#manifest: /location/of/manifest/file

coreos:
  units..."""
        result = self.meta._parse_user_data(cloudconfig)
        self.meta._read_file.assert_called_with('/location/of/manifest/file',
                                                '{}')
        self.assertEqual(result, {'foo': 'bar'})

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

    def test_read_file(self):
        output = AwsMeta._read_file('test/open.test', 'default')
        self.assertEquals('test', output)

    @patch('spacel.aws.meta.open')
    def test_read_file_error(self, mock_open):
        mock_open.side_effect = IOError('Kaboom')
        output = AwsMeta._read_file('test/open.test', 'default')
        self.assertEquals('default', output)

    @patch('spacel.aws.meta.urlopen')
    def test_block_device(self, mock_urlopen):
        mock_urlopen.return_value = StringIO('xvdc')
        instance_id = AwsMeta.block_device(0)
        self.assertEquals('/dev/xvdc', instance_id)

    @patch('spacel.aws.meta.urlopen')
    def test_block_device_translate(self, mock_urlopen):
        mock_urlopen.return_value = StringIO('sdb')
        instance_id = AwsMeta.block_device(0)
        self.assertEquals('/dev/xvdb', instance_id)
