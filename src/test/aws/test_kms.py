import unittest
from mock import MagicMock
from base64 import b64decode

from botocore.exceptions import ClientError

from spacel.aws import ClientCache
from spacel.aws.kms import KmsCrypto
from spacel.security import EncryptedPayload
from test.security.test_payload import IV, KEY, REGION, ENCODING

CIPHERTEXT = b64decode('QMl1jCZiLqXO+aLZhuDO6w==')
PLAINTEXT = 'test secret'


class TestKmsCrypto(unittest.TestCase):
    def setUp(self):
        self.kms = MagicMock()
        self.kms.decrypt.return_value = {
            'Plaintext': KEY
        }
        self.clients = MagicMock(spec=ClientCache)
        self.clients.kms.return_value = self.kms
        self.kms_crypto = KmsCrypto(self.clients)

    def test_decrypt_invalid_key(self):
        invalid_ciphertext = ClientError({'Error': {
            'Message': ('An error occurred (InvalidCiphertextException) when '
                        'calling the Decrypt operation:')
        }}, 'Decrypt')
        self.kms.decrypt.side_effect = invalid_ciphertext

        plain = self.kms_crypto.decrypt(IV, CIPHERTEXT, KEY, REGION, ENCODING)
        self.assertIsNone(plain)

    def test_decrypt(self):
        plain = self.kms_crypto.decrypt(IV, CIPHERTEXT, KEY, REGION, ENCODING)
        self.assertEquals(PLAINTEXT, plain)

    def test_decrypt_bytes(self):
        ciphertext = b64decode('bqeYegh7yY1jrJBEBV5LTA==')
        plain = self.kms_crypto.decrypt(IV, ciphertext, KEY, REGION, 'bytes')
        self.assertEquals(b'01234', plain)

    def test_decrypt_payload(self):
        payload = EncryptedPayload(IV, CIPHERTEXT, KEY, REGION, ENCODING)
        plain = self.kms_crypto.decrypt_payload(payload)
        self.assertEquals(PLAINTEXT, plain)
