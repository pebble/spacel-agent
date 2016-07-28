import unittest
from mock import patch, MagicMock
from spacel.agent.instance import InstanceManager
from spacel.model import AgentManifest


class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.instance = InstanceManager(back_off_scale=0.0001)
        self.manifest = AgentManifest({
            'healthcheck': {
                'endpoint': 'localhost/',
                'virtual_host': 'spacel-agent.com',
                'protocol': 'http',
                'forwarded_protocol': 'https',
                'timeout': 0.01
            }
        })

    def test_health(self):
        self.instance._check_health = MagicMock(return_value=True)
        result = self.instance.health(self.manifest)
        self.assertEqual(result, True)
        self.assertEqual(self.instance._check_health.call_count, 1)

    def test_health_fail(self):
        self.instance._check_health = MagicMock(return_value=False)
        result = self.instance.health(self.manifest)
        self.assertEqual(result, False)
        self.assertEqual(self.instance._check_health.call_count, 8)

    def test_health_no_endpoint(self):
        manifest = AgentManifest({
            'healthcheck': {}
        })
        result = self.instance.health(manifest)
        self.assertEqual(result, True)

    @patch('spacel.agent.instance.urllib2')
    def test_check_health(self, mock_urllib):
        mock_urllib = self.urllib_mock(mock_urllib, 200)
        result = self.instance._check_health(self.manifest.healthcheck)
        self.assertEqual(result, True)
        url = 'http://172.17.0.1/'
        mock_urllib.Request.assert_called_with(url)

    @patch('spacel.agent.instance.urllib2')
    def test_check_health_fail(self, mock_urllib):
        mock_urllib = self.urllib_mock(mock_urllib, 400)
        result = self.instance._check_health(self.manifest.healthcheck)
        self.assertEqual(result, False)
        url = 'http://172.17.0.1/'
        mock_urllib.Request.assert_called_with(url)

    @staticmethod
    def urllib_mock(urllib, status):
        response = MagicMock()
        response.getcode.return_value = int(status)
        request = MagicMock()
        urllib.urlopen.return_value = response
        urllib.Request.return_value = request
        return urllib

    @patch('spacel.agent.instance.urllib2')
    def test_check_health_exception(self, mock_urllib):
        mock_urllib.urlopen.side_effect = Exception('Kaboom')
        result = self.instance._check_health(self.manifest.healthcheck)
        self.assertEqual(result, False)
