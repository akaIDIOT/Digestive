import pytest

from digestive import Source


def test_empty():
    source = Source('test/files/empty')

    assert source.source == 'test/files/empty'
    assert source.fd is None
    assert len(source) == 0

    with source:
        assert source.fd is not None
        assert len(source) == 0
        assert source.readinto(bytearray(32)) == 0

    assert source.fd is None


def test_1234():
    source = Source('test/files/1234')

    assert len(source) == 4

    with source:
        assert len(source) == 4

        buffer = bytearray(32)

        assert source.readinto(buffer) == 4
        assert buffer[:4] == b'\x01\x02\x03\x04'


def test_blocks():
    source = Source('test/files/1234')

    with source:
        for (read, expected) in zip(source.blocks(2), (b'\x01\x02', b'\x03\x04')):
            assert read == expected

    with source:
        generator = source.blocks(2)
        assert next(generator) == b'\x01\x02'
        assert next(generator) == b'\x03\x04'
        with pytest.raises(StopIteration):
            next(generator)
            raise AssertionError('StopIteration should have been raised')
