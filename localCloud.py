import os
import pickle
from flask import jsonify

class LocalCloud:
    def __init__(self, cloudId):
        self.cloudId = cloudId
        self.dirName = 'cloud' + str(self.cloudId)

    def initialize(self):
        if os.path.isdir(self.dirName):
            print("Cloud already exists!")
            return
        os.makedirs(self.dirName)

    def read(self, file):
        filename = os.path.join(self.dirName, file)
        if not os.path.exists(filename):
            return 'None'
        with open(filename, 'rb') as f:
            return jsonify(pickle.load(f))

    def write(self, data, filename):
        filename = os.path.join(self.dirName, filename)
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
