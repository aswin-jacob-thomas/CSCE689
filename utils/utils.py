from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA1
from Crypto.Cipher import AES
import os
from binascii import hexlify, unhexlify


def getSignature(cloudId, unit):
    hashUnit = SHA1.new(unit.encode('utf8'))
    if not os.path.exists('cloudKeys'):
        os.makedirs('cloudKeys')

    filename = 'keyPair' + str(cloudId) + '.pem'
    sig_file = os.path.join('cloudKeys', filename)

    if not os.path.exists(sig_file):
        keyPair = RSA.generate(bits=1024)
        with open(sig_file, 'wb') as f:
            f.write(keyPair.export_key('PEM'))

    with open(sig_file, 'r') as f:
        keyPair = RSA.import_key(f.read())
    signer = PKCS115_SigScheme(keyPair)

    re = hexlify(signer.sign(hashUnit))
    return re


def verifySignature(cloudId, data, signature):
    hashData = SHA1.new(data.encode('utf8'))
    filename = 'keyPair' + str(cloudId) + '.pem'
    sig_file = os.path.join('cloudKeys', filename)
    with open(sig_file, 'r') as f:
        keyPair = RSA.import_key(f.read())
    pubKey = keyPair.publickey()
    signer = PKCS115_SigScheme(pubKey)
    original_sign = unhexlify(signature)

    try:
        signer.verify(hashData, original_sign)
        return True
    except:
        return False


def getHash(value, return_hexdigest=False):
    if return_hexdigest:
        return SHA1.new(value.encode('utf-8')).hexdigest()
    else:
        return SHA1.new(value.encode('utf-8'))


def convert_to_bytes(string):
    return string.encode('utf-8')


def convert_to_string(byte):
    return byte.decode('utf-8')


def getAESCiphers(key):
    iv = b'a\x9e\x9a8\x95\x9a\xf0PS\xa3y\x8e\xae\xe1\xd0\xc1'
    return AES.new(key, AES.MODE_EAX, iv)


def pad(s):
    BS = 16
    return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)


def unpad(s):
    return s[0:-ord(s[-1])]