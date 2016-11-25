import logging

from spacel.agent.mixin.base import BaseMixinWriter

logger = logging.getLogger('spacel')


class SetupCloudWatchLogs(BaseMixinWriter):
    def __init__(self, systemd, meta):
        super(SetupCloudWatchLogs, self).__init__(systemd)
        self._meta = meta

    def logs(self, manifest):
        docker_logging = manifest.logging.get('docker', {})
        log_group = docker_logging.get('group')
        if not log_group:
            logger.debug('Docker logging not configured.')
            return

        self._write_mixin('docker.service', '10-logs', {
            'DOCKER_OPTS': ('--log-driver awslogs' +
                            ' --log-opt awslogs-region=%s' % self._meta.region +
                            ' --log-opt awslogs-group=%s' % log_group)
        })

        logger.debug('Restarting docker.service with CW:L log driver.')
        self._systemd.restart('docker.service')
