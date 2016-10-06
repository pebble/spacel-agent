import unittest

from mock import MagicMock, ANY
from spacel.aws import ClientCache
from spacel.agent.environment import ApplicationEnvironment


class TestApplicationEnvironment(unittest.TestCase):
    def setUp(self):
        self.elasticache = MagicMock()
        self.clients = MagicMock(spec=ClientCache)
        self.clients.elasticache.return_value = self.elasticache
        self.manifest = MagicMock()
        self.app_env = ApplicationEnvironment(self.clients)

    def test_environment(self):
        environment = self.app_env.environment('FOO=bar\n', {'BING': 'baz'})
        self.assertEquals('''BING=baz
FOO=bar''', environment)

    def test_common_environment(self):
        self.app_env._caches = MagicMock()

        self.app_env.common_environment(MagicMock())

        self.app_env._caches.assert_called_with(ANY, ANY)

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
