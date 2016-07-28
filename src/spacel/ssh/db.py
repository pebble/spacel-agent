import logging

logger = logging.getLogger('spacel')

ADMIN_SERVICE_NAME = 'SPACE_ELEVATOR_OPERATORS'


class SshDb(object):
    def __init__(self, clients, meta):
        self.dynamodb = clients.dynamodb()
        self.services_table = '%s-services' % meta.orbit
        self.users_table = '%s-users' % meta.orbit

    def bastion_keys(self, key=None):
        """
        Get every key that can connect to bastion host.
        :param key: Key user is authenticating with.
        :return: SSH keys for authorized users.
        """
        logger.debug('Getting bastion keys.')

        # Collect admins of every service:
        users = set()
        service_paginator = self.dynamodb.get_paginator('scan')
        service_scan = service_paginator.paginate(
            TableName=self.services_table,
            AttributesToGet=['admins'])
        for scan_page in service_scan:
            services = scan_page.get('Items', ())
            for service in services:
                self._add_service_users(users, service)
        users = sorted(list(users))
        logger.debug('Bastion authorizes: %s', users)

        return self._keys(users, key)

    def service_keys(self, name, key=None):
        """
        Get every key that can connect to a service host.
        :param name: Service name.
        :param key: Key user is authenticating with.
        :return: SSH keys for authorized users.
        """
        logger.debug('Getting service keys for "%s".', name)

        # Combine admins of this service with global admins:
        users = set()
        service_keys = [{'name': {'S': ADMIN_SERVICE_NAME}},
                        {'name': {'S': name}}]
        for service in self._batch_get(self.services_table, service_keys,
                                       ['admins']):
            self._add_service_users(users, service)
        users = sorted(list(users))
        logger.debug('Service %s authorizes: %s', name, users)

        return self._keys(users, key)

    def _keys(self, user_set, key):
        if not user_set:
            return []

        keys = set()
        user_items = self._batch_get(self.users_table,
                                     [{'username': {'S': username}}
                                      for username in user_set],
                                     ['username', 'keys'])
        for user in user_items:
            ssh_keys = user.get('keys', {}).get('SS', ())
            logger.debug('Fetched %i SSH keys for %s.', len(ssh_keys),
                         user['username']['S'])
            for user_key in ssh_keys:
                plain_key = user_key.replace('ssh-rsa', '').strip()
                if plain_key == key:
                    return user_key,
                keys.add(user_key)
        return sorted(list(keys))

    def _batch_get(self, table_name, keys, attributes_to_get):
        batch_response = self.dynamodb.batch_get_item(RequestItems={
            table_name: {
                'Keys': keys,
                'AttributesToGet': attributes_to_get
            }
        })
        return batch_response.get('Responses', {}).get(table_name, ())

    @staticmethod
    def _add_service_users(users, service):
        service_admins = service.get('admins', {}).get('SS', ())
        for service_admin in service_admins:
            users.add(service_admin)
