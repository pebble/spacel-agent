import logging

from spacel.agent.mixin.base import BaseMixinWriter

logger = logging.getLogger('spacel')
CW_STATS_SERVICE = 'cloudwatch-stats.service'


class SetupCloudWatchStats(BaseMixinWriter):
    def __init__(self, systemd, instance_tags):
        super(SetupCloudWatchStats, self).__init__(systemd)
        self._instance_tags = instance_tags

    def stats(self, manifest):
        if not manifest.stats:
            logger.debug('CloudWatch stats not enabled.')
            return

        tags = self._instance_tags.get()
        asg = tags.get('aws:autoscaling:groupName')
        # TODO: what about spotfleets?
        if asg:
            self._write_mixin(CW_STATS_SERVICE, '10-asg', {
                'ASG_PARAMS': '--auto-scaling --auto-scaling-group=%s' % asg
            })

        self._systemd.start(CW_STATS_SERVICE)
