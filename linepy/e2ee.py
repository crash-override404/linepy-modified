# -*- coding: utf-8 -*-
from urllib.parse import quote, unquote, urlencode
from collections import namedtuple
from Crypto.Cipher import AES
import base64, hashlib, os
import axolotl_curve25519 as Curve25519

KeyPairCurve = namedtuple('KeyPair', ['private_key', 'public_key', 'nonce'])
AESKeyAndIV = namedtuple('AESKey', ['Key', 'IV'])

class E2EE:

    def __init__(self):
        self.Curve = self.generateKeypair()

    def _xor(self, buf):
        buf_length = int(len(buf) / 2)
        buf2 = bytearray(buf_length)
        for i in range(buf_length):
            buf2[i] = buf[i] ^ buf[buf_length + i]
        return bytes(buf2)

    def _getSHA256Sum(self, *args):
        instance = hashlib.sha256()
        for arg in args:
            if isinstance(arg, str):
                arg = arg.encode()
            instance.update(arg)
        return instance.digest()

    def _encryptAESECB(self, aes_key, plain_data):
        aes = AES.new(aes_key, AES.MODE_ECB)
        return aes.encrypt(plain_data)

    def _decryptAESECB(self, aes_key, encrypted_data):
        aes = AES.new(aes_key, AES.MODE_ECB)
        return aes.decrypt(encrypted_data)

    def _encryptAESCBC(self, aes_key, aes_iv, plain_data):
        aes = AES.new(aes_key, AES.MODE_CBC, aes_iv)
        return aes.encrypt(plain_data)

    def _decrpytAESCBC(self, aes_key, aes_iv, encrypted_data):
        aes = AES.new(aes_key, AES.MODE_CBC, aes_iv)
        return aes.decrypt(encrypted_data)

    def generateKeypair(self):
        private_key = Curve25519.generatePrivateKey(os.urandom(32))
        public_key = Curve25519.generatePublicKey(private_key)
        nonce = os.urandom(16)
        return KeyPairCurve(private_key, public_key, nonce)

    def generateParams(self):
        secret = base64.b64encode(self.Curve.public_key).decode()
        return 'secret={secret}&e2eeVersion=1'.format(secret=quote(secret))

    def generateSharedSecret(self, public_key):
        private_key = self.Curve.private_key
        shared_secret = Curve25519.calculateAgreement(private_key, public_key)
        return shared_secret

    def generateAESKeyAndIV(self, shared_secret):
        aes_key = self._getSHA256Sum(shared_secret, 'Key')
        aes_iv = self._xor(self._getSHA256Sum(shared_secret, 'IV'))
        return AESKeyAndIV(aes_key, aes_iv)

    def generateSignature(self, aes_key, encrypted_data):
        data = self._xor(self._getSHA256Sum(encrypted_data))
        signature = self._encryptAESECB(aes_key, data)
        return signature

    def verifySignature(self, signature, aes_key, encrypted_data):
        data = self._xor(self._getSHA256Sum(encrypted_data))
        return self._decryptAESECB(aes_key, signature) == data

    def decryptKeychain(self, encrypted_keychain, public_key):
        public_key = base64.b64decode(public_key)
        encrypted_keychain = base64.b64decode(encrypted_keychain)
        shared_secret = self.generateSharedSecret(public_key)
        aes_key, aes_iv = self.generateAESKeyAndIV(shared_secret)
        keychain_data = self._decrpytAESCBC(aes_key, aes_iv, encrypted_keychain)
        return keychain_data
