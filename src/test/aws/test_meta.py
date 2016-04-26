import unittest
from StringIO import StringIO
from urllib2 import URLError

from mock import patch
from spacel.aws.meta import AwsMeta


class TestAwsMeta(unittest.TestCase):
    def setUp(self):
        self.awsmeta = AwsMeta()

    @patch('spacel.aws.meta.urlopen')
    def test_get_instance_id(self, mock_urlopen):
        mock_urlopen.return_value = StringIO('i-123456')
        instance_id = self.awsmeta.get_instance_id()
        self.assertEquals('i-123456', instance_id)

    @patch('spacel.aws.meta.urlopen')
    def test_get_instance_id_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('Kaboom')
        instance_id = self.awsmeta.get_instance_id()
        self.assertIn('i-', instance_id)

    @patch('spacel.aws.meta.urlopen')
    def test_get_region(self, mock_urlopen):
        mock_urlopen.return_value = StringIO('us-west-1a')
        region = self.awsmeta.get_region()
        self.assertEquals('us-west-1', region)

    @patch('spacel.aws.meta.urlopen')
    def test_get_region_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('Kaboom')
        region = self.awsmeta.get_region()
        self.assertEquals('us-east-1', region)

    @patch('spacel.aws.meta.urlopen')
    def test_get_user_data(self, mock_urlopen):
        mock_urlopen.return_value = StringIO('{"foo":"bar"}')
        user_data = self.awsmeta.get_user_data()
        self.assertEqual({'foo': 'bar'}, user_data)

    @patch('spacel.aws.meta.urlopen')
    def test_get_user_data_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError('Kaboom')
        user_data = self.awsmeta.get_user_data()
        self.assertEqual({}, user_data)
