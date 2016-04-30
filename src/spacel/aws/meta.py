import json
import time
from urllib2 import urlopen, URLError

INSTANCE_ID_URL = 'http://169.254.169.254/latest/meta-data/instance-id'
PLACEMENT_URL = ('http://169.254.169.254/latest/meta-data/placement/'
                 'availability-zone')
USER_DATA_URL = 'http://169.254.169.254/latest/user-data'


class AwsMeta(object):
    """
    Wraps AWS metadata calls.
    """

    @staticmethod
    def get_instance_id():
        """
        Get instance id.
        :return: Instance id.
        """
        try:
            return urlopen(INSTANCE_ID_URL).read()
        except URLError:
            return 'i-%s' % str(time.time()).replace('.', '')

    @staticmethod
    def get_region():
        """
        Get region.
        :return: Region.
        """
        try:
            az = urlopen(PLACEMENT_URL).read()
            return az[:-1]
        except URLError:
            return 'us-east-1'

    @staticmethod
    def get_user_data():
        """
        Get user data.
        :return: User data.
        """
        try:
            user_data = urlopen(USER_DATA_URL).read()
            # TODO: if url, download
            return json.loads(user_data)
        except URLError:
            return {}
