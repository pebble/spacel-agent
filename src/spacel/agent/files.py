import errno
import logging
import os

logger = logging.getLogger('spacel')


class FileWriter(object):
    """
    Writes files from manifests to disk.
    """

    def __init__(self, home='/files', systemd='/etc/systemd/system'):
        self._home = home
        self._systemd = systemd

    def write_files(self, manifest):
        """
        Write files from manifest to disk.
        :param manifest:  Manifest.
        :return: None
        """
        for fn, file_data in manifest.all_files.items():
            file_path = os.path.join(self._home, fn)

            body = file_data['body']
            body = body.decode('base64')
            # TODO: decryption, KMS?

            logger.debug('Writing "%s".', file_path)
            with open(file_path, 'w') as out:
                out.write(body)

            mode = file_data.get('mode')
            if mode is not None:
                file_mode = int(mode, 8)
                logger.debug('Setting "%s" to %s.', file_path, mode)
                os.chmod(file_path, file_mode)

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
