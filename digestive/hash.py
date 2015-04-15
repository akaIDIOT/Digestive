import hashlib

from digestive.io import Sink


class HashDigest(Sink):
    def __init__(self, name, digest, **kwargs):
        super().__init__(name, **kwargs)
        self._digest = digest

    def process(self, data):
        self._digest.update(data)

    def result(self):
        return self._digest.hexdigest()


class MD5(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('md5', hashlib.md5(), **kwargs)


class SHA1(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('sha1', hashlib.sha1(), **kwargs)


class SHA256(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('sha256', hashlib.sha256(), **kwargs)


class SHA512(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('sha512', hashlib.sha512(), **kwargs)


try:
    # importing sha3 will add sha3 digests to hashlib
    import sha3  # noqa
    sha3_enabled = True
except ImportError:
    sha3_enabled = False


class SHA3256(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('sha3-256', hashlib.sha3_256(), **kwargs)


class SHA3512(HashDigest):
    def __init__(self, **kwargs):
        super().__init__('sha3-512', hashlib.sha3_512(), **kwargs)
