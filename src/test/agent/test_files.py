import unittest
from mock import MagicMock, ANY
import os
import tempfile
import shutil
from spacel.agent import ApplicationEnvironment
from spacel.agent.files import FileWriter
from spacel.model import AgentManifest
from spacel.aws import KmsCrypto

INSTANCE_ID = 'i-123456'
UNIT_FILE = '''[Unit]
Description=Test

[Service]
User=space
TimeoutStartSec=0
Restart=always
StartLimitInterval=0
ExecStartPre=-/usr/bin/docker pull pwagner/http-env-echo:master
ExecStartPre=-/usr/bin/docker kill %n
ExecStartPre=-/usr/bin/docker rm %n
ExecStart=/bin/sh -c "/usr/bin/docker run --rm --name %n -p 80:8080 pwagner/http-env-echo:master > /dev/null 2>&1"
ExecStop=/usr/bin/docker stop %n
'''


class TestFileWriter(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.systemd = tempfile.mkdtemp()
        self.app_env = MagicMock(spec=ApplicationEnvironment)
        self.app_env.environment.return_value = ''
        self.app_env.common_environment.return_value = {}
        self.kms = MagicMock(spec=KmsCrypto)
        self.writer = FileWriter(self.app_env, self.kms, self.home,
                                 self.systemd)
        self.manifest = AgentManifest({
            'files': {
                'foo.txt': {
                    'mode': '0644',
                    'body': 'hello world\n'.encode('base64').strip()
                }
            },
            'systemd': {
                'foo.service': {
                    'body': UNIT_FILE.encode('base64').strip()
                }
            }
        })

    def tearDown(self):
        if os.path.isdir(self.home):
            shutil.rmtree(self.home)
        shutil.rmtree(self.systemd)

    def test_write_files(self):
        self.writer.write_files(self.manifest)
        self.app_env.environment.assert_called_with('', {})

        file_path = os.path.join(self.home, 'foo.txt')
        self.assertTrue(os.path.isfile(file_path))

        service_path = os.path.join(self.home, 'foo.service')
        service_link = os.path.join(self.systemd, 'foo.service')
        self.assertTrue(os.path.isfile(service_path))
        self.assertTrue(os.path.islink(service_link))

    def test_write_files_env(self):
        self.manifest.files['foo.env'] = {
            'body': 'FOO=bar'.encode('base64').strip()
        }

        self.writer.write_files(self.manifest)

        self.app_env.environment.assert_called_once_with('FOO=bar', {})

    def test_write_files_overwrite(self):
        self.writer.write_files(self.manifest)
        self.writer.write_files(self.manifest)

    def test_write_files_error(self):
        shutil.rmtree(self.home)
        self.assertRaises(IOError, self.writer.write_files, self.manifest)

    def test_write_files_decrypt_invalid_payload(self):
        # Ciphertext without accompanying fields is ignored:
        self.manifest.systemd['foo.service']['ciphertext'] = 'meow'

        self.writer.write_files(self.manifest)
        self.kms.decrypt_payload.assert_not_called()

        # 'body' is written:
        service_path = os.path.join(self.home, 'foo.service')
        with open(service_path) as service_in:
            self.assertEquals(UNIT_FILE, service_in.read())

    def test_write_files_decrypt(self):
        # No 'body' provided, but UNIT_FILE returned from "decryption":
        self.kms.decrypt_payload.return_value = UNIT_FILE
        self.manifest.systemd['bar.service'] = {
            'ciphertext': 'test',
            'iv': 'test',
            'key': 'test',
            'key_region': 'us-east-1',
            'encoding': 'bytes'
        }

        self.writer.write_files(self.manifest)

        # Decryption result is written:
        self.kms.decrypt_payload.assert_called_with(ANY)
        service_path = os.path.join(self.home, 'bar.service')
        with open(service_path) as service_in:
            self.assertEquals(UNIT_FILE, service_in.read())
