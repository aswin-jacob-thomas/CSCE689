import requests
import json
from DataUnit import DataUnit
import queue
import threading
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.SecretSharing import Shamir
from pyeclib.ec_iface import ECDriver
from SecretUnit import SecretUnit, SecretUnitEncoder, SecretUnitDecoder
from Metadata import Metadata, MetadataEncoder, MetadataDecoder
from utils import getSignature, getHash, verifySignature, getAESCiphers, pad, unpad
from CloudMetadata import CloudMetadata, CloudMetadataDecoder


class DepSkyClient:
    def __init__(self, clientId, isLocal=True):
        self.clientId = clientId
        self.isLocal = isLocal
        self.N = 4
        self.F = 1
        self.metadataQ = queue.Queue()
        self.ec_driver = ECDriver(k=2, m=2, ec_type='liberasurecode_rs_vand')

        if self.isLocal:
            self.createLocalClients()

    def read(self, container):
        maxVersion, metadata_list = self.getMetadataFromClouds(filename= container.duId + 'metadata')
        count = 0
        if maxVersion == 0:
            print('No data to read! Sorry!!!')
            return
        dataFileName = container.duId + 'value' + str(maxVersion)
        secret_unit_list = self.readDataFromClouds(metadata_list, dataFileName)
        shares = []
        fragments = []
        for unit in secret_unit_list:
            shares.append((unit.secret_id, unit.share))
            fragments.append(unit.value)

        key = Shamir.combine(shares)
        encrypted_data = self.ec_driver.decode(fragments)

        cipher = getAESCiphers(key)
        data = cipher.decrypt(encrypted_data)
        return data

    def readDataFromClouds(self, metadata_list, filename):
        results = self.readInParallel(metadata_list, filename)
        return results

    def readInParallel(self, metadata_list, filename):
        q = queue.Queue()
        cloudIds = [cloudMetadata.cloudId for cloudMetadata in metadata_list]
        threads = [threading.Thread(target=self.getFileFromCloud, args=(i, filename, q)) for i in cloudIds]

        results = []
        verified_count = 0

        for thread in threads:
            thread.daemon = True
            thread.start()

        for _ in range(len(cloudIds)):
            result = q.get()

            result = json.loads(result)
            secretUnit = SecretUnitDecoder().decode(result)
            cloudId = secretUnit.cloudId
            metadata_of_secret_unit = metadata_list[cloudId]
            latest_metadata = metadata_of_secret_unit[0]
            if getHash(secretUnit) == latest_metadata.hashedUnit:
                results.append(secretUnit)
                verified_count += 1

            if verified_count > self.F:
                break

        return results

    def createLocalClients(self):
        for i in range(4):
            requests.post('http://localhost:5555', data=json.dumps({'cloudId': i}))

    def generateKeyShares(self, key):
        return Shamir.split(self.F + 1, self.N, key)

    def erasureCode(self, value):
        return self.ec_driver.encode(value)

    def write(self, container, value):
        maxVersion, metadata_list = self.getMetadataFromClouds(filename= container.duId + 'metadata')
        nextVersion = maxVersion + 1
        value_hash = getHash(value, return_hexdigest = True)
        key = get_random_bytes(16)

        cipher = getAESCiphers(key)
        encrypted_value = cipher.encrypt(value.encode('utf8'))
        shares = self.generateKeyShares(key)
        fragments = self.erasureCode(encrypted_value)

        units = []

        for cloudId, (share, fragment) in enumerate(zip(shares, fragments)):
            idx, secret = share
            unit = SecretUnit(idx, secret, fragment, cloudId)
            units.append(SecretUnitEncoder().encode(unit))

        self.writeToClouds(container.duId +'value'+str(nextVersion), units)
        self.writeMetadata(container.duId +'metadata', value_hash, units, nextVersion, metadata_list)

    def writeToClouds(self, filename, units):
        results = self.writeInParallel(filename, units)

    def writeInParallel(self, filename, dataList):
        q = queue.Queue()
        threads = []
        for i, data in enumerate(dataList):
            threads.append(threading.Thread(target=self.writeToCloud, args=(i, data, filename, q)))
        for thread in threads:
            thread.daemon = True
            thread.start()

        results = []
        for _ in range(self.N - self.F):
            results.append(q.get())
        return results

    def writeToCloud(self, cloudId, data, filename, result_queue):
        r = requests.post('http://localhost:5555/write', data=json.dumps({'cloudId': cloudId, 'data2write': data, 'filename': filename}))
        result_queue.put(r.text)

    def writeMetadata(self, filename, dataHash, units, version, metadata_list):
        metadata_of_clouds = []

        for _ in range(self.F):
            value = self.metadataQ.get()
            if value == 'None':
                metadata_list.append(None)
            else:
                result = json.loads(value)
                cloudMetadata = CloudMetadataDecoder().decode(result)
                metadata_list.append(cloudMetadata)

        for i in range(self.N):
            hashedUnit = getHash(units[i])
            metadata = Metadata(dataHash, hashedUnit.hexdigest(), version, getSignature(i, hashedUnit))

            if metadata_list[i]:
                cloudMetadata = metadata_list[i].add_new_metadata(metadata)
            else:
                cloudMetadata = CloudMetadata([metadata], i)

            cloudMetadata = cloudMetadata.return_writable_content()
            metadata_of_clouds.append(cloudMetadata)

        results = self.writeInParallel(filename, metadata_of_clouds)

    def getMetadataInParallel(self, function, filename):
        q = self.metadataQ
        threads = [threading.Thread(target=function, args=(i, filename,q)) for i in range(4)]
        versions_from_metadata = []

        results = []
        verified_count = 0

        for thread in threads:
            thread.daemon = True
            thread.start()

        for _ in range(self.N):
            result = q.get()
            if result == 'None':
                results.append(None)
            else:
                result = json.loads(result)
                cloudMetadata = CloudMetadataDecoder().decode(result)
                latest_metadata = cloudMetadata.metadata_list[0]
                list_of_dicts = cloudMetadata.return_metadata_list_in_dicts()

                print("The hash from the obtained cloudMetadata of cloud ", cloudMetadata.cloudId)
                print(getHash(list_of_dicts).hexdigest())
                print("The thing of which the hash is taken")
                print(list_of_dicts)

                if verifySignature(cloudMetadata.cloudId, getHash(list_of_dicts), cloudMetadata.metadata_list_sig):
                    if verifySignature(cloudMetadata.cloudId, latest_metadata.hashedUnit, latest_metadata.signature):
                        verified_count += 1
                        versions_from_metadata.append(latest_metadata.version)
                        results.append(cloudMetadata)
                        print("This is verified")
                    else:
                        print("Nooooooo!!!")
                else:
                    print('Noooo')

            # breaking condition
            if not any(results) and len(results) == self.N - self.F:
                break

            if verified_count == self.N - self.F:
                break

        return results, max(versions_from_metadata) if len(versions_from_metadata) > 0 else 0

    def getMetadataFromClouds(self, filename):
        results, maxVersion = self.getMetadataInParallel(self.getFileFromCloud, filename)
        return maxVersion, results

    def getFileFromCloud(self, cloudId, filename, result_queue):
        r = requests.post('http://localhost:5555/read', data=json.dumps({'cloudId': cloudId, 'filename': filename}))
        result_queue.put(r.text)


if __name__ == '__main__':
    client = DepSkyClient(clientId=0, isLocal=True)
    print("Pick a data unit- pick_du")
    print("Read - read")
    print("Write - write 'sample text'")
    while True:
        text = input('Please provide an input\n')
        if 'pick_du' in text:
            container_name = text[8:]
            if len(container_name) == 0:
                print('Please provide a valid name')
                continue
            du = DataUnit(container_name)
            print('Data unit ', du, 'created')
        elif du and 'write' in text:
            content = text[6:]
            client.write(du, content)
            print('Write complete')
        elif du and 'read' in text:
            client.read(du)
