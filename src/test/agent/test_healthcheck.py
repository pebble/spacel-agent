import unittest
from mock import MagicMock
from spacel.agent.healthcheck import BaseHealthCheck


class TestBaseHealthCheck(unittest.TestCase):
    def setUp(self):
        self.check_params = {}
        self.health_check = BaseHealthCheck(0.00001)

    def test_check_healthy(self):
        health = self.health_check._check(self.check_params, lambda: True)
        self.assertTrue(health)

    def test_check_time_out(self):
        self.check_params['timeout'] = 0.001
        health = self.health_check._check(self.check_params, lambda: False)
        self.assertFalse(health)

    def test_check_exceed_max_retries(self):
        self.check_params['max_retries'] = 2
        predicate = MagicMock(return_value=False)
        health = self.health_check._check(self.check_params, predicate)
        self.assertFalse(health)
        self.assertEquals(2, predicate.call_count)
