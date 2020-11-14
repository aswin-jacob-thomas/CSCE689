from utils.utils import getSignature, getHash, convert_to_bytes, convert_to_string
from models.Metadata import MetadataDecoder, MetadataEncoder
import json
from copy import deepcopy

class CloudMetadata:
    def __init__(self, metadata_list, cloudId, metadata_list_sig=None):
        self.cloudId = cloudId
        self.metadata_list = metadata_list
        self.metadata_list_sig = metadata_list_sig

    def add_new_metadata(self, metadata):
        self.metadata_list.insert(0, metadata)
        return self

    def return_metadata_list_in_dicts(self):
        return json.dumps([MetadataEncoder().encode(m) for m in self.metadata_list])

    def return_writable_content(self):
        list_dict = self.return_metadata_list_in_dicts()
        metadataHash = getHash(list_dict).hexdigest()
        encoded_cloud_metadata = deepcopy(self)
        # print('Writing cloud metadata!!!')
        # print('The Details at the time of writing of cloud', self.cloudId)
        # print("The list of dicts is ")
        # print(list_dict)
        encoded_cloud_metadata.metadata_list_sig = convert_to_string(getSignature(self.cloudId, metadataHash))

        metadata_dict_list = []
        for metadata in self.metadata_list:
            metadata_dict_list.append(MetadataEncoder().encode(metadata))
        encoded_cloud_metadata.metadata_list = metadata_dict_list
        return encoded_cloud_metadata.__dict__


class CloudMetadataDecoder:
    def decode(self, ob):
        metadata_list_sig = convert_to_bytes(ob['metadata_list_sig'])
        metadata_list = ob['metadata_list']
        cloudId = ob['cloudId']
        decoded_list = []
        for metadata in metadata_list:
            decoded_list.append(MetadataDecoder().decode(metadata))
        return CloudMetadata(decoded_list, cloudId, metadata_list_sig)