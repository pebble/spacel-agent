import unittest

from mock import MagicMock, ANY
from spacel.aws import ClientCache, KmsCrypto, AwsMeta
from spacel.agent.environment import ApplicationEnvironment
from test.security import PAYLOAD

CIPHER_ENV = 'FOO=%s' % PAYLOAD.json()

DB_USERNAME = 'root'
DB_PASSWORD = 'supersecret'
DB_ADDRESS = 'foo.rds.com'
DB_PORT = 5432
DB_NAME = 'test'
DB_URL = 'postgres://root:supersecret@foo.rds.com:5432/test'
REGION = 'us-east-1'
DATABASE_PARAMETERS = {
    DB_NAME: {
        'name': 'test-db-instance',
        'region': REGION,
        'password': PAYLOAD.obj()
    }
}


class TestApplicationEnvironment(unittest.TestCase):
    def setUp(self):
        self.elasticache = MagicMock()
        self.rds = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.clients.elasticache.return_value = self.elasticache
        self.clients.rds.return_value = self.rds
        self.kms = MagicMock(spec=KmsCrypto)
        self.meta = MagicMock(spec=AwsMeta)
        self.meta.region = REGION
        self.manifest = MagicMock()
        self.app_env = ApplicationEnvironment(self.clients, self.meta, self.kms)

    def test_environment(self):
        environment = self.app_env.environment('FOO=bar\n', {'BING': 'baz'})
        self.assertEquals('''BING=baz
FOO=bar''', environment)

    def test_environment_crypt_key_invalid_decrypt(self):
        self.kms.decrypt_payload.return_value = None
        environment = self.app_env.environment(CIPHER_ENV, {})
        self.assertEquals(CIPHER_ENV, environment)

    def test_environment_crypt_key_wrong_key(self):
        """
        Verify decrypted env entries start with the entry key.
        This defends against copying a secret value to a key that's exposed
        (i.e. `PASSWORD`->`APP_VERSION`)
        """
        self.kms.decrypt_payload.return_value = 'BAR=decrypted'
        environment = self.app_env.environment(CIPHER_ENV, {})
        self.assertEquals(CIPHER_ENV, environment)

    def test_environment_crypt_key(self):
        self.kms.decrypt_payload.return_value = 'FOO=decrypted'
        environment = self.app_env.environment(CIPHER_ENV, {})
        self.assertEquals('FOO=decrypted', environment)

    def test_common_environment(self):
        self.app_env._caches = MagicMock()
        self.app_env._databases = MagicMock()

        self.app_env.common_environment(MagicMock())

        self.app_env._caches.assert_called_with(ANY, ANY)
        self.app_env._databases.assert_called_with(ANY, ANY)

    def test_caches_not_found(self):
        self.elasticache.describe_replication_groups.return_value = {
            'ReplicationGroups': []
        }
        self.manifest.caches = {'test': 'test-replication-group'}
        env = {}

        self.app_env._caches(self.manifest, env)
        self.assertEquals(0, len(env))

    def test_caches(self):
        self.elasticache.describe_replication_groups.return_value = {
            'ReplicationGroups': [{
                'NodeGroups': [{
                    'PrimaryEndpoint': {
                        'Address': '127.0.0.1',
                        'Port': '6379'
                    },
                    'NodeGroupMembers': [{
                        'ReadEndpoint': {
                            'Address': '127.0.0.2',
                            'Port': '6379'
                        }
                    }]
                }]
            }]
        }
        self.manifest.caches = {'test': 'test-replication-group'}
        env = {}

        self.app_env._caches(self.manifest, env)
        self.assertEquals({
            'TEST_URL': 'redis://127.0.0.1:6379',
            'TEST_URL_00': 'redis://127.0.0.2:6379'
        }, env)

    def test_databases_not_found(self):
        self.manifest.databases = DATABASE_PARAMETERS
        self.rds.describe_db_instances.return_value = {
            'DBInstances': []
        }

        env = {}
        self.app_env._databases(self.manifest, env)

        self.assertEquals({}, env)

    def test_databases(self):
        self.manifest.databases = DATABASE_PARAMETERS
        self.rds.describe_db_instances.return_value = {
            'DBInstances': [{
                'MasterUsername': DB_USERNAME,
                'DBName': DB_NAME,
                'Endpoint': {
                    'Address': DB_ADDRESS,
                    'Port': DB_PORT
                }
            }]
        }
        self.kms.decrypt_payload.return_value = DB_PASSWORD

        env = {}
        self.app_env._databases(self.manifest, env)

        self.assertEquals({
            'TEST_HOSTNAME': DB_ADDRESS,
            'TEST_PORT': DB_PORT,
            'TEST_USERNAME': DB_USERNAME,
            'TEST_PASSWORD': DB_PASSWORD,
            'TEST_DATABASE': DB_NAME,
            'TEST_URL': DB_URL
        }, env)
