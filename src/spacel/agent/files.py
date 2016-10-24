import errno
import logging
import os
from spacel.security import EncryptedPayload

logger = logging.getLogger('spacel')


class FileWriter(object):
    """
    Writes files from manifests to disk.
    """

    def __init__(self, app_env, kms, home='/files',
                 systemd='/etc/systemd/system'):
        self._app_env = app_env
        self._kms = kms
        self._home = home
        self._systemd = systemd

    def write_files(self, manifest):
        """
        Write files from manifest to disk.
        :param manifest:  Manifest.
        :return: None
        """
        common_env = self._app_env.common_environment(manifest)
        services = set()
        environments = set()
        for fn, file_data in manifest.all_files.items():
            file_path = os.path.join(self._home, fn)

            body = None
            if 'ciphertext' in file_data:
                payload = EncryptedPayload.from_obj(file_data)
                if payload:
                    body = self._kms.decrypt_payload(payload)

            # Fallback to plaintext:
            if not body:
                body = file_data['body']
                body = body.decode('base64')

            if file_path.endswith('.env'):
                environments.add(fn.replace('.env', ''))
                body = self._app_env.environment(body, common_env)
            elif file_path.endswith('.service'):
                services.add(fn.replace('.service', ''))

            logger.debug('Writing "%s".', file_path)
            with open(file_path, 'w') as out:
                out.write(body)

            mode = file_data.get('mode')
            if mode is not None:
                file_mode = int(mode, 8)
                logger.debug('Setting "%s" to %s.', file_path, mode)
                os.chmod(file_path, file_mode)

        services_without_environment = services - environments
        if services_without_environment:
            common_env = self._app_env.environment('', common_env)
            for service in services_without_environment:
                env_path = os.path.join(self._home, '%s.env' % service)
                with open(env_path, 'w') as out:
                    out.write(common_env)

        for fn in manifest.systemd.keys():
            file_path = os.path.join(self._home, fn)
            systemd_path = os.path.join(self._systemd, fn)
            logger.debug('Linking "%s".', systemd_path)
            try:
                os.symlink(file_path, systemd_path)
            except OSError, e:
                if e.errno != errno.EEXIST:  # pragma: no cover
                    raise e
                os.remove(systemd_path)
                os.symlink(file_path, systemd_path)
