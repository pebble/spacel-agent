import logging
import time
import urllib2
import sys

logger = logging.getLogger('spacel')


class InstanceManager(object):
    """
    Perform actions directly on this instance.
    """

    def __init__(self, back_off_scale=0.1):
        self._back_off_scale = back_off_scale

    def health(self, manifest, timeout=900):
        """
        Healthcheck an endpoint from the manifest for timeout in s
        :param manifest:  Manifest.
        :param timeout:  Timeout.
        :return: Health status (boolean)
        """
        if not manifest.healthcheck.get('endpoint'):
            return True

        retries = 0
        start = time.time()
        while True:
            if self._check_health(manifest.healthcheck):
                return True

            if (time.time() - start) > timeout:
                return False
            back_off = (2 ** retries) * self._back_off_scale
            back_off = min(back_off, 10)
            retries += 1
            time.sleep(back_off)

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
        except:
            e = sys.exc_info()[0]
            logger.info('Failed to execute healthcheck on "%s"', url)
            logger.exception(e)
            return False
