import logging
import unittest

from mock import MagicMock, patch, ANY

from spacel.aws import ClientCache, AwsMeta
from spacel.log import parse_level, setup_watchtower, DEFAULT_CWL_LEVEL
from spacel.model import AgentManifest

LOG_GROUP = 'test-log-group'
INSTANCE_ID = 'i-123456789012'


class TestLogging(unittest.TestCase):
    def setUp(self):
        self.clients = MagicMock(spec=ClientCache)
        self.meta = MagicMock(spec=AwsMeta)
        self.meta.instance_id = INSTANCE_ID
        self.manifest = AgentManifest({})

    def test_parse_level_not_found(self):
        level = parse_level(None, DEFAULT_CWL_LEVEL)
        self.assertEquals(DEFAULT_CWL_LEVEL, level)

    def test_parse_level_invalid(self):
        level = parse_level('meow', DEFAULT_CWL_LEVEL)
        self.assertEquals(DEFAULT_CWL_LEVEL, level)

    def test_parse_level_case(self):
        level = parse_level('warning', DEFAULT_CWL_LEVEL)
        self.assertEquals(logging.WARNING, level)

    def test_parse_level(self):
        level = parse_level('INFO', DEFAULT_CWL_LEVEL)
        self.assertEquals(logging.INFO, level)

    @patch('spacel.log.watchtower')
    @patch('spacel.log.open')
    def test_setup_watchtower_noop(self, mock_open, watchtower):
        setup_watchtower(self.clients, self.meta, self.manifest)
        watchtower.CloudWatchLogHandler.assert_not_called()
        mock_open.assert_not_called()

    @patch('spacel.log.watchtower')
    def test_setup_watchtower_path(self, watchtower):
        self.manifest.logging = {
            'deploy': {
                'group': 'path:test/open.test'
            }
        }
        setup_watchtower(self.clients, self.meta, self.manifest)
        watchtower.CloudWatchLogHandler.assert_called_once_with(
            log_group='test',
            boto3_session=self.clients,
            use_queues=ANY,
            send_interval=ANY,
            create_log_group=False,
            stream_name=INSTANCE_ID
        )

    @patch('spacel.log.watchtower')
    @patch('spacel.log.open')
    def test_setup_watchtower(self, mock_open, watchtower):
        self.manifest.logging = {
            'deploy': {
                'group': LOG_GROUP,
                'level': 'DEBUG'
            }
        }
        setup_watchtower(self.clients, self.meta, self.manifest)
        watchtower.CloudWatchLogHandler.assert_called_once_with(
            log_group=LOG_GROUP,
            boto3_session=self.clients,
            use_queues=ANY,
            send_interval=ANY,
            create_log_group=False,
            stream_name=INSTANCE_ID
        )
        mock_open.assert_not_called()
