import hashlib

from digestive.io import Sink


class HashDigest(Sink):
    def __init__(self, name, digest):
        super().__init__(name)
        self._digest = digest

    def process(self, data):
        self._digest.update(data)

    def result(self):
        return self._digest.hexdigest()


class MD5(HashDigest):
    def __init__(self):
        super().__init__('md5', hashlib.md5())


class SHA1(HashDigest):
    def __init__(self):
        super().__init__('sha1', hashlib.sha1())


class SHA256(HashDigest):
    def __init__(self):
        super().__init__('sha256', hashlib.sha256())


class SHA512(HashDigest):
    def __init__(self):
        super().__init__('sha512', hashlib.sha512())
