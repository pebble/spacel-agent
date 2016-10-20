import logging

from Crypto.Cipher import AES
from Crypto.Util.py3compat import bchr, bord

logger = logging.getLogger('spacel')

CIPHER_MODE = AES.MODE_CBC


class KmsCrypto(object):
    def __init__(self, clients):
        self._clients = clients

    def decrypt_payload(self, payload):
        """
        Decrypt an encrypted payload.
        :param payload: EncryptedPayload.
        :return: Decrypted payload.
        """
        return self.decrypt(payload.iv, payload.ciphertext, payload.key,
                            payload.key_region, payload.encoding)

    def decrypt(self, iv, ciphertext, key, key_region, encoding):
        """
        Decrypt.
        :param iv: Encryption IV.
        :param ciphertext:  Ciphertext.
        :param key: Encrypted data key.
        :param key_region: Data key region (KMS).
        :param encoding:  Encoding
        :return: Decrypted payload.
        """
        try:
            # Decrypt DEK:
            logger.debug('Decrypting data key...')
            kms = self._clients.kms(key_region)
            decrypted_key = kms.decrypt(CiphertextBlob=key)

            # Decrypt data:
            cipher = AES.new(decrypted_key['Plaintext'], CIPHER_MODE, iv)
            plaintext = cipher.decrypt(ciphertext)

            # Remove pad:
            pad_length = bord(plaintext[-1])
            actual_pad = plaintext[-pad_length:]
            expected_pad = bchr(pad_length) * pad_length
            if actual_pad != expected_pad:  # pragma: no cover
                raise ValueError('Incorrect padding')
            unpadded = plaintext[:-pad_length]

            if encoding == 'bytes':
                return unpadded
            return unpadded.decode(encoding)
        except Exception as e:
            logger.warn('Decryption exception %s', e)
            return None
