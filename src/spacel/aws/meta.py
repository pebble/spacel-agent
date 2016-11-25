import json
from time import time
from urllib2 import urlopen, URLError

from spacel.aws.helpers import read_file

INSTANCE_DATA = 'http://instance-data/latest/'
INSTANCE_ID_URL = INSTANCE_DATA + 'meta-data/instance-id'
PLACEMENT_URL = INSTANCE_DATA + 'meta-data/placement/availability-zone'
USER_DATA_URL = INSTANCE_DATA + 'user-data'
BLOCK_DEVICES_URL = INSTANCE_DATA + 'meta-data/block-device-mapping/'

DEFAULT_INSTANCE = 'i-%s' % str(time()).replace('.', '')


class AwsMeta(object):
    def __init__(self):
        # Metadata service:
        self.instance_id = self._get(INSTANCE_ID_URL, DEFAULT_INSTANCE)
        self.az = self._get(PLACEMENT_URL, 'us-east-1a')
        self.region = self.az[:-1]

        # User-data
        self.user_data = self._parse_user_data(self._get(USER_DATA_URL, '{}'))
        self.name = self.user_data.get('name', 'test')
        self.orbit = self.user_data.get('orbit', 'test')
        self.bastion = self.user_data.get('bastion', False)

    @staticmethod
    def _parse_user_data(data):
        # Backward compat: UserData may be a YAML, with a comment referencing
        # local manifest file path.
        split = data.splitlines()
        for line in split:
            if line.startswith('#manifest:'):
                location = line.replace('#manifest:', '').strip()
                return json.loads(read_file(location, '{}'))

        return json.loads(data)

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
