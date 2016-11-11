from spacel.security.payload import EncryptedPayload

IV = b'0000000000000000'
CIPHERTEXT = b'0000000000000000'
KEY = b'0000000000000000'
ENCODING = 'utf-8'
REGION = 'us-east-1'

PAYLOAD = EncryptedPayload(IV, CIPHERTEXT, KEY, REGION, ENCODING)
