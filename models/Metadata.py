from utils.utils import convert_to_string, convert_to_bytes
import copy


class Metadata:
    def __init__(self, dataHash, hashedUnit, version, signature):
        self.dataHash = dataHash
        self.hashedUnit = hashedUnit
        self.version = version
        self.signature = signature


class MetadataDecoder:
    def decode(self, ob):
        return Metadata(ob['dataHash'], ob['hashedUnit'], ob['version'], convert_to_bytes(ob['signature']))


class MetadataEncoder:
    def encode(self, ob):
        encoded_metadata = copy.deepcopy(ob)
        encoded_metadata.signature = convert_to_string(ob.signature)
        return encoded_metadata.__dict__
