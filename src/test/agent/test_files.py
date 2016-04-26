import unittest
import os
import tempfile
import shutil
from spacel.agent.files import FileWriter
from spacel.model import AgentManifest


class TestFileWriter(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        self.systemd = tempfile.mkdtemp()
        self.writer = FileWriter(self.home, self.systemd)
        self.manifest = AgentManifest({
            'files': {
                'foo.txt': {
                    'mode': '0644',
                    'body': 'hello world\n'.encode('base64').strip()
                }
            },
            'systemd': {
                'foo.service': {
                    'body': '''[Unit]
Description=Test

[Service]
User=jenkins
TimeoutStartSec=0
Restart=always
StartLimitInterval=0
ExecStartPre=-/usr/bin/docker pull pwagner/http-env-echo:master
ExecStartPre=-/usr/bin/docker kill %n
ExecStartPre=-/usr/bin/docker rm %n
ExecStart=/bin/sh -c "/usr/bin/docker run --rm --name %n -p 80:8080 pwagner/http-env-echo:master > /dev/null 2>&1"
ExecStop=/usr/bin/docker stop %n
'''.encode('base64').strip()
                }
            }
        })

    def tearDown(self):
        if os.path.isdir(self.home):
            shutil.rmtree(self.home)
        shutil.rmtree(self.systemd)

    def test_write_files(self):
        self.writer.write_files(self.manifest)

        file_path = os.path.join(self.home, 'foo.txt')
        self.assertTrue(os.path.isfile(file_path))

        service_path = os.path.join(self.home, 'foo.service')
        service_link = os.path.join(self.systemd, 'foo.service')
        self.assertTrue(os.path.isfile(service_path))
        self.assertTrue(os.path.islink(service_link))

    def test_write_files_overwrite(self):
        self.writer.write_files(self.manifest)
        self.writer.write_files(self.manifest)

    def test_write_files_error(self):
        shutil.rmtree(self.home)
        self.assertRaises(IOError, self.writer.write_files, self.manifest)
