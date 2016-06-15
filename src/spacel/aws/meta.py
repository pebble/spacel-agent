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
        self.user_data = self._parse_user_data(self._get(USER_DATA_URL, '{}'))
        self.name = self.user_data.get('name', 'test')
        self.orbit = self.user_data.get('orbit', 'test')
        self.bastion = self.user_data.get('bastion', False)

    def _parse_user_data(self, data):
        split = data.splitlines()
        for line in split:
            if line.startswith('#manifest:'):
                location = line.replace('#manifest:', '').strip()
                return json.loads(self._read_file(location, '{}'))

        return json.loads(data)

    @staticmethod
    def _get(url, default):
        try:
            return urlopen(url).read()
        except URLError:
            return default

    @staticmethod
    def _read_file(path, default):
        try:
            with open(path) as file_in:
                return file_in.read()
        except IOError:
            return default

    @staticmethod
    def block_device(block_device):
        block_device_url = '%s/ephemeral%s' % (BLOCK_DEVICES_URL, block_device)

        device = AwsMeta._get(block_device_url, None)
        if device[:2] == 'sd':
            return '/dev/xvd%s' % device[-1:]
        else:
            return '/dev/%s' % device
