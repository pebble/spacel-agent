import logging

from spacel.security import EncryptedPayload

logger = logging.getLogger('spacel')


class ApplicationEnvironment(object):
    def __init__(self, clients, meta, kms_crypto):
        self._clients = clients
        self._region = meta.region
        self._kms_crypto = kms_crypto

    def environment(self, base_env, common_env):
        env = common_env.copy()
        for base_line in base_env.split('\n'):
            if '=' not in base_line:
                continue
            key, value = base_line.split('=', 1)
            env[key] = self._decrypt(key, value)
        env.update(common_env)

        return '\n'.join('%s=%s' % (key, value)
                         for key, value in sorted(env.items()))

    def _decrypt(self, key, value):
        """
        Decrypt value (if it is a JSON-encoded EncryptedPayload)
        :param key: Environment key.
        :param value: Value.
        :return: Decrypted payload; original value on error.
        """
        payload = EncryptedPayload.from_json(value)
        if not payload:
            return value

        decrypted = self._kms_crypto.decrypt_payload(payload)
        if not decrypted:
            return value

        key_prefix = '%s=' % key
        if not decrypted.startswith(key_prefix):
            return value

        return decrypted[len(key_prefix):]

    def common_environment(self, manifest):
        """
        Return common environment settings.
        :param manifest: Application manifest.
        :return: Common environment settings as dict
        """
        env = {}
        self._caches(manifest, env)
        self._databases(manifest, env)
        return env

    def _caches(self, manifest, env):
        elasticache = self._clients.elasticache()
        for name, replication_group in manifest.caches.items():
            replication_groups = elasticache.describe_replication_groups(
                ReplicationGroupId=replication_group
            ).get('ReplicationGroups')

            if not replication_groups:
                logger.warning('Replication group %s (%s) not found.',
                               replication_group, name)
                continue

            name = name.upper()
            for node_group in replication_groups[0]['NodeGroups']:
                env['%s_URL' % name] = \
                    self._redis_url(node_group['PrimaryEndpoint'])
                for index, member in enumerate(node_group['NodeGroupMembers']):
                    env['%s_URL_%02d' % (name, index)] = \
                        self._redis_url(member['ReadEndpoint'])

    @staticmethod
    def _redis_url(node):
        return 'redis://%s:%s' % (node['Address'], node['Port'])

    def _databases(self, manifest, env):
        for name, db_params in manifest.databases.items():
            db_name = db_params['name']
            db_region = db_params.get('region', self._region)

            rds = self._clients.rds(db_region)
            db_instances = (rds.describe_db_instances(
                DBInstanceIdentifier=db_name
            )['DBInstances'])

            if not db_instances:
                logger.warning('Database instance %s (%s) not found.',
                               db_name, name)
                continue
            db_instances = db_instances[0]

            db_username = db_instances['MasterUsername']
            db_password = db_params.get('password', '')
            if 'ciphertext' in db_password:
                payload = EncryptedPayload.from_obj(db_password)
                if payload:
                    db_password = self._kms_crypto.decrypt_payload(payload)

            db_name = db_instances['DBName']
            db_endpoint = db_instances['Endpoint']
            db_hostname = db_endpoint['Address']
            db_port = db_endpoint['Port']
            db_url = 'postgres://%s:%s@%s:%s/%s' % (db_username, db_password,
                                                    db_hostname, db_port,
                                                    db_name)

            name = name.upper()
            env['%s_USERNAME' % name] = db_username
            env['%s_PASSWORD' % name] = db_password
            env['%s_HOSTNAME' % name] = db_hostname
            env['%s_PORT' % name] = db_port
            env['%s_DATABASE' % name] = db_name
            env['%s_URL' % name] = db_url
