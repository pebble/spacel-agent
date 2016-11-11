import unittest

from spacel.security.payload import EncryptedPayload
from test.security import IV, CIPHERTEXT, KEY, ENCODING, REGION, PAYLOAD


class TestEncryptedPayload(unittest.TestCase):
    def test_from_json(self):
        payload = EncryptedPayload.from_json('''{
            "ciphertext": "MDAwMDAwMDAwMDAwMDAwMA==",
            "encoding": "utf-8",
            "iv": "MDAwMDAwMDAwMDAwMDAwMA==",
            "key": "MDAwMDAwMDAwMDAwMDAwMA==",
            "key_region": "us-east-1"
        }''')
        self.assertTestPayload(payload)

    def test_from_json_not_json(self):
        payload = EncryptedPayload.from_json('meow')
        self.assertIsNone(payload)

    def test_from_json_invalid_json(self):
        payload = EncryptedPayload.from_json('{}')
        self.assertIsNone(payload)

    def test_json_round_trip(self):
        as_json = PAYLOAD.json()
        self.assertIsInstance(as_json, str)
        from_json = EncryptedPayload.from_json(as_json)
        self.assertTestPayload(from_json)

    def assertTestPayload(self, payload):
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)
