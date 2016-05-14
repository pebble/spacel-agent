from mock import MagicMock, ANY
from spacel.ssh.db import SshDb
from test.aws import MockedClientTest, INSTANCE_ID, AVAILABILITY_ZONE

NAME = 'test-service'
SERVICES_TABLE_NAME = 'services'
USERS_TABLE_NAME = 'users'


class TestSshDb(MockedClientTest):
    def setUp(self):
        super(TestSshDb, self).setUp()
        self.ssh_db = SshDb(self.clients)

    def test_bastion_keys(self):
        self.ssh_db._keys = MagicMock()
        user_items = [
            {'admins': {'SS': ['admin1']}},
            {'admins': {'SS': ['admin1', 'admin2']}}
        ]

        scan_paginator = MagicMock()
        scan_paginator.paginate.return_value = [
            {'Items': user_items}]
        self.dynamodb.get_paginator.return_value = scan_paginator

        self.ssh_db.bastion_keys()

        self.ssh_db._keys.assert_called_with(['admin1', 'admin2'], ANY)

    def test_service_keys(self):
        self.ssh_db._keys = MagicMock()
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                SERVICES_TABLE_NAME: [
                    {'admins': {'SS': ['admin1']}},
                    {'admins': {'SS': ['admin1', 'admin2']}}
                ]
            }
        }

        self.ssh_db.service_keys(NAME)

        self.ssh_db._keys.assert_called_with(['admin1', 'admin2'], ANY)

    def test_keys(self):
        self._mock_keys()

        keys = self.ssh_db._keys(['admin1', 'admin2'], None)

        self.assertEqual(['ssh-rsa 1', 'ssh-rsa 2', 'ssh-rsa 3', 'ssh-rsa 4'],
                         keys)

    def test_keys_short_circuit(self):
        self._mock_keys()

        keys = self.ssh_db._keys(['admin1', 'admin2'], '1')

        self.assertEqual(('ssh-rsa 1',), keys)

    def _mock_keys(self):
        self.dynamodb.batch_get_item.return_value = {
            'Responses': {
                USERS_TABLE_NAME: [
                    {'keys': {'SS': ['ssh-rsa 1', 'ssh-rsa 2']}},
                    {'keys': {'SS': ['ssh-rsa 3', 'ssh-rsa 4']}},
                ]
            }
        }
