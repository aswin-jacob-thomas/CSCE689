import requests
import json
from DataUnit import DataUnit
import queue
import threading
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.SecretSharing import Shamir
from pyeclib.ec_iface import ECDriver
from SecretUnit import SecretUnit, SecretUnitEncoder

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

    def generateKeyShares(self, key):
        return Shamir.split(self.F + 1, self.N, key)

    def erasureCode(self, value):
        ec_driver = ECDriver(k=2, m=2, ec_type='liberasurecode_rs_vand')
        return ec_driver.encode(value)

    def write(self, container, value):
        nextVersion = self.getMetadataFromClouds()
        # value_hash = hashlib.sha1(value).hexdigest()
        key = get_random_bytes(16)
        # print(key)
        # exit(0)
        cipher = AES.new(key, AES.MODE_EAX)
        print(value)
        print(type(value))
        encrypted_value = cipher.encrypt(value.encode('utf8'))
        shares = self.generateKeyShares(key)
        fragments = self.erasureCode(encrypted_value)

        units = []
        for fragment, share in zip(shares, fragments):
            units.append(SecretUnit(str(share), str(fragment)))

        self.writeToClouds(container.duId +'value'+str(nextVersion), units)

    def writeToClouds(self, filename, secretUnits):
        results = self.writeInParallel(filename, secretUnits)

    def writeInParallel(self, filename, secretUnits):
        q = queue.Queue()
        threads = []
        for i, unit in enumerate(secretUnits):
            encoded_unit = SecretUnitEncoder().encode(unit)
            threads.append(threading.Thread(target=self.writeToCloud, args=(i, encoded_unit, filename,q)))
        for thread in threads:
            thread.daemon = True
            thread.start()

        results = []
        for _ in range(self.N - self.F):
            results.append(q.get())
        return results

    def writeToCloud(self, cloudId, secretUnit, filename,result_queue):
        r = requests.post('http://localhost:5555/write', data=json.dumps({'cloudId': cloudId, 'data2write': secretUnit, 'filename': filename}))
        result_queue.put(r.text)

    def sendInParallel(self, function):
        q = queue.Queue()
        threads = [threading.Thread(target=function, args=(i, q)) for i in range(4)]
        for thread in threads:
            thread.daemon = True
            thread.start()

        results = []
        for _ in range(self.N - self.F):
            results.append(q.get())
        return results

    def getMetadataFromClouds(self):
        results = self.sendInParallel(self.getMetadataFromCloud)
        maxVersion = -1
        if not any(results):
            maxVersion = 0
        # TO-DO: check for max version from the returned metadata file
        nextVersion = maxVersion + 1
        return nextVersion

    def getMetadataFromCloud(self, cloudId, result_queue):
        r = requests.post('http://localhost:5555/read', data=json.dumps({'cloudId': cloudId}))
        result_queue.put(r.text)


if __name__ == '__main__':
    client = DepSkyClient(clientId=0, isLocal=True)
    print("Pick a data unit- pick_du\n")
    print("Read - read\n")
    print("Write - write 'sample text'\n")
    while True:
        text = input('Please provide an input\n')
        if 'pick_du' in text:
            container_name = text[8:]
            du = DataUnit(container_name)
            print('Data unit ', du, 'created')
        elif du and 'write' in text:
            content = text[6:]
            client.write(du, content)
