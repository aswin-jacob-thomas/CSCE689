import requests
import json
from DataUnit import DataUnit
import queue
import threading
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.SecretSharing import Shamir

class DepSkyClient:
    def __init__(self, clientId, isLocal=True):
        self.clientId = clientId
        self.isLocal = isLocal
        self.N = 4
        self.F = 1

        if self.isLocal:
            self.createLocalClients()

    def createLocalClients(self):
        for i in range(4):
            requests.post('http://localhost:5555', data=json.dumps({'cloudId': i}))

    def generateKeyShares(self):
        pass

    def write(self, value):
        nextVersion = self.getMetadataFromClouds()
        value_hash = hashlib.sha1(value).hexdigest()
        key = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_value = cipher.encrypt(value)
        shares = Shamir.split(self.F+1, self.N, key)



    def getMetadataFromClouds(self):
        q = queue.Queue()
        threads = [threading.Thread(target=self.getMetadataFromCloud, args=(i, q)) for i in range(4)]
        for thread in threads:
            thread.daemon = True
            thread.start()

        results = []
        for _ in range(self.N-self.F):
            results.append(q.get())

        maxVersion = -1
        if not any(results):
            maxVersion = 0
        nextVersion = maxVersion + 1
        return nextVersion

    def getMetadataFromCloud(self, cloudId, result_queue):
        r = requests.post('http://localhost:5555/read', data=json.dumps({'cloudId': cloudId}))
        result_queue.put(r.text)

if __name__ == '__main__':
    client = DepSkyClient(clientId=0, isLocal=True)
    print("Pick a data unit- pick_du")
    print("Read - read")
    print("Write - write 'sample text'")
    while True:
        text = input('Please provide an input')
        if 'pick_du' in text:
            container_name = text[8:]
            du = DataUnit(container_name)
            print('Data unit ', du, 'created')
        elif du and 'write' in text:
            content = text[6:]
            client.write(content)


