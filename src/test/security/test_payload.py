import unittest
from spacel.security.payload import EncryptedPayload

IV = b'0000000000000000'
CIPHERTEXT = b'0000000000000000'
KEY = b'0000000000000000'
ENCODING = 'utf-8'
REGION = 'us-east-1'


class TestEncryptedPayload(unittest.TestCase):
    def test_from_json(self):
        payload = EncryptedPayload.from_json('''{
            "ciphertext": "MDAwMDAwMDAwMDAwMDAwMA==",
            "encoding": "utf-8",
            "iv": "MDAwMDAwMDAwMDAwMDAwMA==",
            "key": "MDAwMDAwMDAwMDAwMDAwMA==",
            "key_region": "us-east-1"
        }''')
        self.assertEquals(IV, payload.iv)
        self.assertEquals(CIPHERTEXT, payload.ciphertext)
        self.assertEquals(KEY, payload.key)
        self.assertEquals(REGION, payload.key_region)
        self.assertEquals(ENCODING, payload.encoding)

    def test_from_json_exception(self):
        payload = EncryptedPayload.from_json('{}')
        self.assertIsNone(payload)
