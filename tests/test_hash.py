from os import path

from digestive.hash import MD5, SHA1, SHA256, SHA512
from digestive.io import Source


here = path.dirname(path.abspath(__file__))


def test_empty():
    sinks = [MD5(), SHA1(), SHA256(), SHA512()]
    with Source(path.join(here, 'files/empty')) as source:
        buffer = bytearray(0)
        source.readinto(buffer)

        for sink in sinks:
            sink.process(buffer)

    hashes = [
        # md5sum files/empty
        'd41d8cd98f00b204e9800998ecf8427e',
        # sha1sum files/empty
        'da39a3ee5e6b4b0d3255bfef95601890afd80709',
        # sha256sum files/empty
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        # sha512sum files/empty
        'cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce'
        '47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e',
    ]
    for (result, expected) in zip((sink.result() for sink in sinks), hashes):
        assert result == expected


def test_1234():
    sinks = [MD5(), SHA1(), SHA256(), SHA512()]
    with Source(path.join(here, 'files/1234')) as source:
        buffer = bytearray(4)
        source.readinto(buffer)
        for sink in sinks:
            sink.process(buffer)

    hashes = [
        # md5sum files/1234
        '08d6c05a21512a79a1dfeb9d2a8f262f',
        # sha1sum files/1234
        '12dada1fff4d4787ade3333147202c3b443e376f',
        # sha256sum files/1234
        '9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a',
        # sha512sum files/1234
        'a7c976db1723adb41274178dc82e9b777941ab201c69de61d0f2bc6d27a3598f'
        '594fa748e50d88d3c2bf1e2c2e72c3cfef78c3c6d4afa90391f7e33ababca48e',
    ]
    for (result, expected) in zip((sink.result() for sink in sinks), hashes):
        assert result == expected


def test_zeroes():
    class FourBlocksSource(Source):  # convenience class to read 4 blocks of any requested size from /dev/zero
        def __init__(self):
            super().__init__('/dev/zero')
            self.num_blocks = 4

        def readinto(self, buffer):
            if self.num_blocks > 0:
                self.num_blocks -= 1
                return super().readinto(buffer)
            else:
                return 0

        def close(self):
            super().close()
            self.num_blocks = 4

    sinks = [MD5(), SHA1(), SHA256(), SHA512()]
    with FourBlocksSource() as source:
        for block in source.blocks(4096):
            for sink in sinks:
                sink.process(block)

    hashes = [
        # md5sum <( dd if=/dev/zero bs=4096 count=4 )
        'ce338fe6899778aacfc28414f2d9498b',
        # sha1sum <( dd if=/dev/zero bs=4096 count=4 )
        '897256b6709e1a4da9daba92b6bde39ccfccd8c1',
        # sha256sum <( dd if=/dev/zero bs=4096 count=4 )
        '4fe7b59af6de3b665b67788cc2f99892ab827efae3a467342b3bb4e3bc8e5bfe',
        # sha512sum <( dd if=/dev/zero bs=4096 count=4 )
        '6eb7f16cf7afcabe9bdea88bdab0469a7937eb715ada9dfd8f428d9d38d86133'
        '945f5f2f2688ddd96062223a39b5d47f07afc3c48d9db1d5ee3f41c8d274dccf',
    ]
    for (result, expected) in zip((sink.result() for sink in sinks), hashes):
        assert result == expected


def test_random():
    sinks = [MD5(), SHA1(), SHA256(), SHA512()]
    with Source(path.join(here, 'files/random.dd')) as source:
        buffer = bytearray(1 << 20)
        source.readinto(buffer)
        for sink in sinks:
            sink.process(buffer)

    hashes = [
        # md5sum files/random.dd
        '257f5c2913ea856cb0a2313f167452d4',
        # sha1sum files/random.dd
        '2f8a9e749cc8e46bebe602827228e76611346f54',
        # sha256sum files/random.dd
        '810ec5f2086379f0e8000456dbf2aede8538fbc9d9898835f114c8771ed834b5',
        # sha512sum files/random.dd
        '24dbb6cb56757a621fb8e6a8c8733f1cfc3c77bd23ac325e672eaaf856eac602'
        '307541ac434f598afb62448e90b3608344cfeb2e64778d3f7024bc69f5bb46ef',
    ]
    for (result, expected) in zip((sink.result() for sink in sinks), hashes):
        assert result == expected
