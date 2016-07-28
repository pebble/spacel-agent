import time


def get_int(params, key, default):
    try:
        return int(params.get(key))
    except:
        return default


def get_float(params, key, default):
    try:
        return float(params.get(key))
    except:
        return default


class BaseHealthCheck(object):
    def __init__(self, back_off_scale):
        self._back_off_scale = back_off_scale

    def _check(self, health_check, predicate, *args):
        timeout = get_float(health_check, 'timeout', 900)
        max_interval = get_float(health_check, 'max_interval', 10)
        max_retries = get_int(health_check, 'max_retries', -1)

        retries = 0
        start = time.time()
        while retries < max_retries or max_retries < 0:
            if predicate(*args):
                return True

            if (time.time() - start) > timeout:
                return False
            back_off = (2 ** retries) * self._back_off_scale
            back_off = min(back_off, max_interval)
            retries += 1
            time.sleep(back_off)
        return False
