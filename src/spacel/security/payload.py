from base64 import b64decode
import json


class EncryptedPayload(object):
    def __init__(self, iv, ciphertext, key, key_region, encoding):
        self.iv = iv
        self.ciphertext = ciphertext
        self.key = key
        self.key_region = key_region
        self.encoding = encoding

    @staticmethod
    def from_json(json_string):
        json_obj = json.loads(json_string)
        return EncryptedPayload.from_obj(json_obj)

    @staticmethod
    def from_obj(payload_obj):
        try:
            return EncryptedPayload(
                b64decode(payload_obj['iv']),
                b64decode(payload_obj['ciphertext']),
                b64decode(payload_obj['key']),
                payload_obj['key_region'],
                payload_obj['encoding'],
            )
        except:
            return None
