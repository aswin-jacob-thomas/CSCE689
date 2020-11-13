from utils import getSignature, getHash, convert_to_bytes, convert_to_string
from Metadata import MetadataDecoder, MetadataEncoder
import json


class CloudMetadata:
    def __init__(self, metadata_list, cloudId, metadata_list_sig=None):
        self.cloudId = cloudId
        self.metadata_list = metadata_list
        self.metadata_list_sig = metadata_list_sig

    def __repr__(self):
        print('called!')
        print(self.__dict__)

    def add_new_metadata(self, metadata):
        self.metadata_list.insert(0, metadata)
        return self

    def return_metadata_list_in_dicts(self):
        return json.dumps([MetadataEncoder().encode(m) for m in self.metadata_list])

    def return_writable_content(self):
        list_dict = self.return_metadata_list_in_dicts()
        metadataHash = getHash(list_dict)
        print('The metadatahash at the time of writing of cloud', self.cloudId)
        print(metadataHash.hexdigest())
        self.metadata_list_sig = convert_to_string(getSignature(self.cloudId, metadataHash))
        print('The signature at the time of writing')
        print(self.metadata_list_sig)
        print("The thing of which the hash is taken")
        print(list_dict)

        metadata_dict_list = []
        for metadata in self.metadata_list:
            metadata_dict_list.append(MetadataEncoder().encode(metadata))
        self.metadata_list = metadata_dict_list
        return self.__dict__


class CloudMetadataDecoder:
    def decode(self, ob):
        metadata_list_sig = convert_to_bytes(ob['metadata_list_sig'])
        metadata_list = ob['metadata_list']
        cloudId = ob['cloudId']
        decoded_list = []
        for metadata in metadata_list:
            decoded_list.append(MetadataDecoder().decode(metadata))
        return CloudMetadata(decoded_list, cloudId, metadata_list_sig)