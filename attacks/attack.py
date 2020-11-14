import os
import pickle
import json

"""
Modify one of the cloud's metadata
Read should work file
"""


def corrupt_one_metadata():
    cloudId = input('Please enter the cloudId\n')
    file = os.path.join('../cloud'+cloudId, 'dumetadata')
    with open(file, 'rb') as f:
        cloudMetadata = pickle.load(f)
    metadata_list_sig = cloudMetadata['metadata_list_sig']
    metadata_list_sig = metadata_list_sig[::-1]
    cloudMetadata['metadata_list_sig'] = metadata_list_sig

    with open(file, 'wb') as f:
        pickle.dump(cloudMetadata, f)
    print('Corrupted the signature of metadata list of cloud', cloudId)


def corrupt_one_data():
    cloudId = input('Please enter the cloudId\n')
    valueFileName = input('Please provide the filename of the data to be corrupted\n')
    file = os.path.join('../cloud'+cloudId, valueFileName)
    with open(file, 'rb') as f:
        secretUnit = json.loads(pickle.load(f))

    secretUnitValue = secretUnit['value']
    secretUnitValue = secretUnitValue[::-1]
    secretUnit['value'] = secretUnitValue

    with open(file, 'wb') as f:
        pickle.dump(json.dumps(secretUnit), f)
    print('Corrupted the data of the cloud', cloudId)


if __name__ == '__main__':
    while True:
        choiceOptions = 'Input corresponding numbers to corrupt metadata and values\n1. Corrupt one metadata\n2. Corrupt one data\n3. Stop\n'
        choice = int(input(choiceOptions))
        if choice == 1:
            corrupt_one_metadata()
        elif choice == 2:
            corrupt_one_data()
        else:
            break
