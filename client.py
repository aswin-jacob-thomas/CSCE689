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
from queue import Empty


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
        # Flush the metadata queue - cancel the remaining requests
        try:
            while True:
                self.metadataQ.get_nowait()
        except Empty:
            pass
        # Flushing complete

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

        print('These are the final shares after combining')
        print(shares)
        print('These are the final fragments from ec')
        print(fragments)

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
        metadata_list_to_dict = {metadata.cloudId: metadata for metadata in metadata_list}
        results = []
        verified_count = 0

        for thread in threads:
            thread.daemon = True
            thread.start()

        for _ in range(len(cloudIds)):
            result = q.get()
            print('Hey im the origianl result', result, type(result))
            result = json.loads(result)
            secretUnit = SecretUnitDecoder().decode(result)
            cloudId = secretUnit.cloudId
            metadata_of_secret_unit = metadata_list_to_dict[cloudId]
            print('The metadata from the cloud being compared - cloudId ', metadata_of_secret_unit.cloudId)
            print('The hash of the thing being taken is ',SecretUnitEncoder().encode(secretUnit))
            latest_metadata = metadata_of_secret_unit.metadata_list[0]
            print('The hash from the metadata to compare with the new hash', latest_metadata.hashedUnit)
            if getHash(SecretUnitEncoder().encode(secretUnit)).hexdigest() == latest_metadata.hashedUnit:
                results.append(secretUnit)
                verified_count += 1
            else:
                print('Not verified..... bad things happens@@')

            if verified_count > self.F:
                # remove the remaining items from the queue
                try:
                    while True:
                        q.get_nowait()
                except Empty:
                    pass

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
        print('Writing aha')
        print('The shares are')
        print(shares)
        print('The fragments are')
        print(fragments)
        units = []

        for cloudId, (share, fragment) in enumerate(zip(shares, fragments)):
            idx, secret = share
            unit = SecretUnit(idx, secret, fragment, cloudId)
            units.append(SecretUnitEncoder().encode(unit))
            print('Writing ', units[cloudId], 'to the cloud', cloudId)

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

        # sort the metadata - or better store as dict :)
        cloudsPresent = any(metadata_list)
        if cloudsPresent:
            metadata_list_to_dict = {metadata.cloudId: metadata for metadata in metadata_list}

        for i in range(self.N):
            print('Writing metadata of ', units[i], 'to cloud', i)
            hashedUnit = getHash(units[i]).hexdigest()
            print('The written hash is ', hashedUnit)
            # got the cloud in ascending order

            metadata = Metadata(dataHash, hashedUnit, version, getSignature(i, hashedUnit))
            if cloudsPresent:
                cloud = metadata_list_to_dict[i]
                cloudMetadata = cloud.add_new_metadata(metadata)
            else:
                cloudMetadata = CloudMetadata([metadata], i)
            print('Now the cloud metadata looks like ')
            print(cloudMetadata.return_writable_content())
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

                # print("The hash from the obtained cloudMetadata of cloud ", cloudMetadata.cloudId)
                # print(getHash(list_of_dicts).hexdigest())
                # print("The thing of which the hash is taken")
                # print(list_of_dicts)

                if verifySignature(cloudMetadata.cloudId, getHash(list_of_dicts).hexdigest(), cloudMetadata.metadata_list_sig):
                    if verifySignature(cloudMetadata.cloudId, latest_metadata.hashedUnit, latest_metadata.signature):
                        verified_count += 1
                        versions_from_metadata.append(latest_metadata.version)
                        results.append(cloudMetadata)
                        print("This is verified of cloud ",cloudMetadata.cloudId)
                    else:
                        print("The whole verification failed!!! of cloud ,", cloudMetadata.cloudId)
                else:
                    print('The first verification failed! of cloud ', cloudMetadata.cloudId)

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
            data = client.read(du)
            print('Hip hip hooray', data)
