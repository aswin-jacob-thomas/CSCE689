from json import JSONEncoder
from utils import convert_to_bytes, convert_to_string
from binascii import hexlify, unhexlify


class SecretUnit:
    def __init__(self, idx, share, value, cloudId):
        self.secret_id = idx
        self.share = convert_to_string(hexlify(share))
        self.value = convert_to_string(hexlify(value))
        self.cloudId = cloudId


class SecretUnitEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class SecretUnitDecoder:
    def decode(self, ob):
        secret_id = ob['secret_id']
        share = convert_to_bytes(unhexlify(ob['share']))
        value = convert_to_bytes(unhexlify(ob['value']))
        cloudId = ob['cloudId']
        return SecretUnit(secret_id, share, value, cloudId)

