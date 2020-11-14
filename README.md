# CSCE689
Python implementation of Depsky - cloud of clouds

Implemented the Depsky-CA protocol for availability and Confidentiality.
## Steps to run the protocol
### Install dependencies
  - Install dependencies - requests, pycryptodome, flask, pickle
  - Install liberasure from https://github.com/openstack/liberasurecode#build-and-install
  - Install pyeclib (for erasure coding) from https://github.com/openstack/pyeclib#installation
### Start flask server
````
python localServer.py
````
### Start the depsky local client
````
python client.py
````
### Protocols
#### Write
  - pick a container for writing (if not already picked)
  `pick_du` **`container_name`**
  - write content_to_write
  `write`**`content_to_write`**
  
#### Read
  - pick a container for reading (if not already picked)
  `pick_du` **`container_name`**
  - read 
  `read`
  
## How to test the protocol
### Run the attack
```
cd attacks
python attacks.py
```
- Choose option 1 to modify the metadata
- Choose option 2 to modify the data stored in the cloud 

