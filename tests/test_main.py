from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from mock import Mock
from os import path

from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA512
from digestive.io import Source
from digestive.main import file_size, parse_arguments, process_arguments, process_source


here = path.dirname(path.abspath(__file__))


def test_file_size():
    assert file_size(0) == '0 bytes'
    assert file_size(999) == '999 bytes'
    assert file_size(1023) == '1023 bytes'
    assert file_size(1024) == '1 KiB'
    assert file_size(1025) == '1.001 KiB'
    assert file_size(1536) == '1.5 KiB'
    assert 'KiB' in file_size(4 << 10)
    assert 'MiB' in file_size(4 << 20)
    assert 'GiB' in file_size(4 << 30)
    assert 'TiB' in file_size(4 << 40)
    assert 'PiB' in file_size(4 << 50)
    assert 'EiB' in file_size(4 << 60)
    assert 'ZiB' in file_size(4 << 70)
    assert 'bytes' in file_size(4 << 80)


def test_process_arguments():
    parser = Mock()
    args = Namespace()
    args.sinks = []
    args.jobs = None

    process_arguments(args, parser)
    parser.error.assert_called_with('at least one sink is required')

    args.sinks = [1, 2, 3]

    process_arguments(args, parser)
    assert args.jobs == 3

    args.jobs = 1

    process_arguments(args, parser)
    assert args.jobs == 1


def test_parse_arguments():
    arguments = ['-m125', 'source1', 'source2']
    arguments = parse_arguments(arguments)

    assert MD5 in arguments.sinks
    assert SHA1 in arguments.sinks
    assert SHA256 in arguments.sinks
    assert SHA512 in arguments.sinks
    assert 'source1' in arguments.sources
    assert 'source2' in arguments.sources
    assert arguments.jobs == 4

    arguments = ['--entropy', '-j', '8', 'source']
    arguments = parse_arguments(arguments)

    assert Entropy in arguments.sinks
    assert arguments.jobs == 8
    assert 'source' in arguments.sources


def test_process_source():
    with ThreadPoolExecutor(2) as executor:
        source = Source(path.join(here, 'files/empty'))
        sink = Mock()
        with source:
            process_source(executor, source, [sink])

        assert not sink.called

        source = Source(path.join(here, 'files/1234'))
        with source:
            process_source(executor, source, [sink])

        sink.update.assert_called_once_with(b'\x01\x02\x03\x04')

        sink.reset_mock()
        with source:
            process_source(executor, source, [sink], block_size=1)

        assert sink.update.call_count == 4

# TODO: test main()
