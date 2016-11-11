import json
from base64 import b64decode, b64encode


class EncryptedPayload(object):
    def __init__(self, iv, ciphertext, key, key_region, encoding):
        self.iv = iv
        self.ciphertext = ciphertext
        self.key = key
        self.key_region = key_region
        self.encoding = encoding

    def json(self):
        return json.dumps({
            'iv': b64encode(self.iv),
            'key': b64encode(self.key),
            'key_region': self.key_region,
            'ciphertext': b64encode(self.ciphertext),
            'encoding': self.encoding,
        }, sort_keys=True)

    @staticmethod
    def from_json(json_string):
        try:
            json_obj = json.loads(json_string)
        except ValueError:
            return None
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
