from os import path

from digestive.entropy import Entropy
from digestive.io import Source


here = path.dirname(path.abspath(__file__))


def test_empty():
    sink = Entropy()
    with Source(path.join(here, 'files/empty')) as source:
        buffer = bytearray(0)
        source.readinto(buffer)

        sink.update(buffer)

    # empty file has 0.0 entropy
    assert float(sink.digest()) == 0.0


def test_range():
    sink = Entropy()

    sink.update(bytearray(range(0, 256)))

    # full range of byte values should be 8.0
    assert float(sink.digest()) == 8.0
