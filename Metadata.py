from json import JSONEncoder


class Metadata:
    def __init__(self, dataHash, encodedUnit, version):
        self.dataHash = dataHash
        self.encodedUnit = encodedUnit
        self.version = version


class MetadataEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__