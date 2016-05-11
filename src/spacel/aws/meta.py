import json
from time import time
from urllib2 import urlopen, URLError

INSTANCE_ID_URL = 'http://169.254.169.254/latest/meta-data/instance-id'
PLACEMENT_URL = ('http://169.254.169.254/latest/meta-data/placement/'
                 'availability-zone')
USER_DATA_URL = 'http://169.254.169.254/latest/user-data'
BLOCK_DEVICES_URL = ('http://169.254.169.254/latest/meta-data/'
                     'block-device-mapping/')

DEFAULT_INSTANCE = 'i-%s' % str(time()).replace('.', '')


class AwsMeta(object):
    def __init__(self):
        self.instance_id = self._get(INSTANCE_ID_URL, DEFAULT_INSTANCE)
        self.az = self._get(PLACEMENT_URL, 'us-east-1a')
        self.region = self.az[:-1]
        self.user_data = json.loads(self._get(USER_DATA_URL, '{}'))

    @staticmethod
    def _get(url, default):
        try:
            return urlopen(url).read()
        except URLError:
            return default

    @staticmethod
    def block_device(block_device):
        block_device_url = '%s/ephemeral%s' % (BLOCK_DEVICES_URL, block_device)

        device = AwsMeta._get(block_device_url, None)
        if device[:2] == 'sd':
            return '/dev/xvd%s' % device[-1:]
        else:
            return '/dev/%s' % device
