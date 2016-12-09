import json

from spacel.model import AgentManifest
from spacel.security import EncryptedPayload


class AgentManifestFactory(object):
    def __init__(self, kms):
        self._kms = kms

    def manifest(self, params):
        params = self._decrypt(params)
        return AgentManifest(params)

    def _decrypt(self, params):
        encrypted_payload = EncryptedPayload.from_obj(params)
        if encrypted_payload is None:
            return params

        decrypted = self._kms.decrypt(encrypted_payload)
        if decrypted is None:
            return params

        return json.loads(decrypted)
