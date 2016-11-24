import unittest

from mock import MagicMock

from spacel.agent.mixin.cloudwatch_stats import (SetupCloudWatchStats,
                                                 CW_STATS_SERVICE)

ASG_NAME = 'test-asg'


class TestSetupCloudWatchStats(unittest.TestCase):
    def setUp(self):
        self.systemd = MagicMock()
        self.instance_tags = MagicMock()
        self.instance_tags.get.return_value = {
            'aws:autoscaling:groupName': ASG_NAME
        }
        self.stats = SetupCloudWatchStats(self.systemd, self.instance_tags)
        self.stats._write_mixin = MagicMock()
        self.manifest = MagicMock()

    def test_stats_disabled(self):
        self.manifest.stats = False

        self.stats.stats(self.manifest)

        self.stats._write_mixin.assert_not_called()
        self.systemd.start.assert_not_called()

    def test_stats_cloudwatch(self):
        self.manifest.stats = True

        self.stats.stats(self.manifest)

        self.stats._write_mixin.assert_called_once_with(
            CW_STATS_SERVICE, '10-asg', {
                'ASG_PARAMS': '--auto-scaling --auto-scaling-group=test-asg'
            })
        self.systemd.start.assert_called_with(CW_STATS_SERVICE)
