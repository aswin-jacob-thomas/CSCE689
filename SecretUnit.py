from json import JSONEncoder


class SecretUnit:
    def __init__(self, share, value):
        self.share = share
        self.value = value


class SecretUnitEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

