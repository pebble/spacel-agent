import unittest

from mock import MagicMock, ANY

from spacel.aws import KmsCrypto
from spacel.model import AgentManifest
from spacel.model.manifest_factory import AgentManifestFactory
from test.security import PAYLOAD


class TestAgentManifestFactory(unittest.TestCase):
    def setUp(self):
        self._kms = MagicMock(spec=KmsCrypto)
        self._amf = AgentManifestFactory(self._kms)

    def test_manifest_plaintext(self):
        manifest = self._amf.manifest({})
        self.assertIsInstance(manifest, AgentManifest)
        self._kms.decrypt.assert_not_called()

    def test_manifest_encrypted(self):
        self._kms.decrypt.return_value = '{}'
        manifest = self._amf.manifest(PAYLOAD.obj())
        self.assertIsInstance(manifest, AgentManifest)
        self._kms.decrypt.assert_called_with(ANY)

    def test_manifest_decryption_failure(self):
        self._kms.decrypt.return_value = None
        manifest = self._amf.manifest(PAYLOAD.obj())
        self.assertIsInstance(manifest, AgentManifest)
