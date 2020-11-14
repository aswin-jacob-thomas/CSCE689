from json import dumps, loads
from utils.utils import convert_to_string
from binascii import hexlify, unhexlify
from copy import deepcopy


class SecretUnit:
    def __init__(self, idx, share, value, cloudId):
        self.secret_id = idx
        self.share = share
        self.value = value
        self.cloudId = cloudId


class SecretUnitEncoder:
    def encode(self, ob):
        encoded_secret_unit = deepcopy(ob)
        encoded_secret_unit.share = convert_to_string(hexlify(ob.share))
        encoded_secret_unit.value = convert_to_string(hexlify(ob.value))
        return dumps(encoded_secret_unit.__dict__)


class SecretUnitDecoder:
    def decode(self, ob):
        ob = loads(ob)
        # print('Im the secret', ob)
        # print('I M OF TYPE', type(ob))
        secret_id = ob['secret_id']
        share = unhexlify(ob['share'])
        value = unhexlify(ob['value'])
        cloudId = ob['cloudId']
        return SecretUnit(secret_id, share, value, cloudId)

