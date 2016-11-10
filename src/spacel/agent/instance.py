import logging
import urllib2
from spacel.agent.healthcheck import BaseHealthCheck

logger = logging.getLogger('spacel')


class InstanceManager(BaseHealthCheck):
    """
    Perform actions directly on this instance.
    """

    def __init__(self, back_off_scale=0.1):
        super(InstanceManager, self).__init__(back_off_scale)

    def health(self, manifest):
        """
        Healthcheck an endpoint from the manifest for timeout in s
        :param manifest:  Manifest.
        :return: Health status (boolean)
        """
        healthcheck = manifest.healthcheck
        if not healthcheck.get('endpoint'):
            return True

        return self._check(healthcheck, self._check_health, healthcheck)

    @staticmethod
    def _check_health(healthcheck):
        """
        Check health of a service.
        :param endpoint: Host + Path.
        :param virtual_host: Virtual host.
        :param protocol: Protocol.
        :return: Health check status (boolean)
        """
        endpoint = healthcheck.get('endpoint')
        # we need to ping the host container
        endpoint = (endpoint.replace('localhost', '172.17.0.1')
                    .replace('127.0.0.1', '172.17.0.1'))
        virtual_host = healthcheck.get('virtual_host', 'localhost')
        protocol = healthcheck.get('protocol', 'http')
        forwarded_protocol = healthcheck.get('forwarded_protocol', 'https')

        url = '%s://%s' % (protocol, endpoint)
        try:
            req = urllib2.Request(url)
            req.add_header('Host', str(virtual_host))
            req.add_header('X-Forwarded-Proto', str(forwarded_protocol))
            resp = urllib2.urlopen(req)
            return resp.getcode() == 200

        except urllib2.URLError as e:
            logger.error(e.reason)
            return False
        except Exception as e:
            logger.info('Failed to execute healthcheck on "%s"', url)
            logger.error(e.message)
            return False
