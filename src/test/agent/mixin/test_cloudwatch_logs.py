import unittest

from mock import MagicMock

from spacel.agent.mixin.cloudwatch_logs import SetupCloudWatchLogs

ASG_NAME = 'test-asg'


class TestSetupCloudWatchLogs(unittest.TestCase):
    def setUp(self):
        self.systemd = MagicMock()
        self.instance_tags = MagicMock()
        self.instance_tags.get.return_value = {
            'aws:autoscaling:groupName': ASG_NAME
        }
        self.meta = MagicMock()
        self.meta.region = 'us-east-1'
        self.logs = SetupCloudWatchLogs(self.systemd, self.meta)
        self.logs._write_mixin = MagicMock()
        self.manifest = MagicMock()

    def test_logs_noop(self):
        self.manifest.logging = {}

        self.logs.logs(self.manifest)

        self.logs._write_mixin.assert_not_called()
        self.systemd.restart.assert_not_called()

    def test_logs(self):
        self.manifest.logging = {
            'docker': {'group': 'test-group'}
        }

        self.logs.logs(self.manifest)

        self.logs._write_mixin.assert_called_once_with(
            'docker.service', '10-logs', {
                'DOCKER_OPTS': '--log-driver awslogs'
                               ' --log-opt awslogs-region=us-east-1'
                               ' --log-opt awslogs-group=test-group'
            })
        self.systemd.restart.assert_called_once_with('docker.service')
