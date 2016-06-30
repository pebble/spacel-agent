from mock import MagicMock, patch
import unittest

from spacel.aws import AwsMeta
from spacel.cli.keys import get_keys
from spacel.ssh.db import SshDb

SERVICE_NAME = 'test'


class TestSshClient(unittest.TestCase):
    @patch('spacel.cli.keys.ClientCache')
    @patch('spacel.cli.keys.AwsMeta')
    @patch('spacel.cli.keys.SshDb')
    def test_keys_bastion(self, sshdb_constructor, meta_constructor, _):
        self._setup_mocks(meta_constructor, sshdb_constructor)
        self.mock_meta.bastion = True

        get_keys()

        self.mock_db.bastion_keys.assert_called_with()
        self.mock_db.service_keys.assert_not_called()

    @patch('spacel.cli.keys.ClientCache')
    @patch('spacel.cli.keys.AwsMeta')
    @patch('spacel.cli.keys.SshDb')
    def test_keys_service(self, sshdb_constructor, meta_constructor, _):
        self._setup_mocks(meta_constructor, sshdb_constructor)
        self.mock_meta.bastion = False

        get_keys()

        self.mock_db.bastion_keys.assert_not_called()
        self.mock_db.service_keys.assert_called_with(SERVICE_NAME)

    def _setup_mocks(self, meta_constructor, sshdb_constructor):
        self.mock_db = MagicMock(spec=SshDb)
        sshdb_constructor.return_value = self.mock_db

        self.mock_meta = MagicMock(spec=AwsMeta)
        self.mock_meta.region = 'us-east-1'
        self.mock_meta.name = SERVICE_NAME

        meta_constructor.return_value = self.mock_meta
