from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from os import path

from mock import ANY, call, MagicMock, Mock, patch
import pytest

from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA512, sha3_enabled, SHA3256, SHA3512
from digestive.io import Source
from digestive.main import file_size, main, num_bytes, parse_arguments, process_arguments, process_source, Progress


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


def test_num_bytes():
    assert num_bytes('123') == 123
    assert num_bytes('123b') == 123
    assert num_bytes('123M') == 123 << 20
    assert num_bytes('123m') == 123 << 20

    with pytest.raises(TypeError):
        # 123 ludicribytes is not a thing...
        num_bytes('123l')


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
    assert arguments.block_size == 1 << 20
    assert not arguments.recursive

    arguments = ['--entropy', '-j', '8', 'source']
    arguments = parse_arguments(arguments)

    assert Entropy in arguments.sinks
    assert arguments.jobs == 8
    assert 'source' in arguments.sources

    arguments = ['-e', '--block-size', '4M', '-r', 'source']
    arguments = parse_arguments(arguments)

    assert Entropy in arguments.sinks
    assert arguments.block_size == 4 << 20
    assert arguments.recursive

    if sha3_enabled:
        arguments = ['--hashes', 'source']
        arguments = parse_arguments(arguments)

        assert SHA3256 in arguments.sinks

        arguments = ['--sha3-512', 'source']
        arguments = parse_arguments(arguments)

        assert SHA3512 in arguments.sinks


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

        sink.process.assert_called_once_with(b'\x01\x02\x03\x04')

        sink.reset_mock()
        with source:
            process_source(executor, source, [sink], block_size=1)

        assert sink.process.call_count == 4


def test_process_source_progress():
    with ThreadPoolExecutor(2) as executor:
        source = Source(path.join(here, 'files/1234'))
        sink = Mock()
        progress = Mock(spec=Progress)

        with source:
            process_source(executor, source, [sink], block_size=3, progress=progress)

        progress.set.assert_has_calls([call(3), call(4)])


def test_main():
    with patch('builtins.print') as mocked_print:
        arguments = ['--hashes', '--output', '/dev/null', path.join(here, 'files/empty'), path.join(here, 'files/1234')]
        main(arguments)
        # assert a few of the prints that should have been made
        mocked_print.assert_any_call('{} ({})'.format(path.join(here, 'files/empty'), '0 bytes'), flush=True)
        mocked_print.assert_any_call('  sha256       e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
        mocked_print.assert_any_call('{} ({})'.format(path.join(here, 'files/1234'), '4 bytes'), flush=True)
        mocked_print.assert_any_call('  sha256       9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a')

    with patch('builtins.print'), patch('digestive.main.output_to_file') as output:
        output_generator = MagicMock()
        output.return_value = output_generator
        # force raw format to treat random.E01 as a regular file (courtesy of Travis…)
        arguments = ['--hashes', '--recursive', '--output', '/dev/null', path.join(here, 'files')]
        main(arguments)
        # assert recursing into files and processing the test files, posting results to output
        output.assert_called_with('/dev/null')
        output_generator.send.assert_has_calls([
            # initial info call
            call({'digestive': '0.1', 'started': ANY}),
            # hashes of tests/files/1234
            call({
                'source': ANY,
                'size': 4,
                'completed': ANY,
                'md5': '08d6c05a21512a79a1dfeb9d2a8f262f',
                'sha1': '12dada1fff4d4787ade3333147202c3b443e376f',
                'sha256': '9f64a747e1b97f131fabb6b447296c9b6f0201e79fb3c5356e6c77e89b6a806a',
                'sha512': 'a7c976db1723adb41274178dc82e9b777941ab201c69de61d0f2bc6d27a3598f594fa748e50d88d3c2bf1e2c2e72c3cfef78c3c6d4afa90391f7e33ababca48e',
                'sha3-256': 'a6885b3731702da62e8e4a8f584ac46a7f6822f4e2ba50fba902f67b1588d23b',
            }),
            # hashes of tests/files/random.dd
            call({
                'source': ANY,
                'size': 1048576,
                'completed': ANY,
                'md5': '257f5c2913ea856cb0a2313f167452d4',
                'sha1': '2f8a9e749cc8e46bebe602827228e76611346f54',
                'sha256': '810ec5f2086379f0e8000456dbf2aede8538fbc9d9898835f114c8771ed834b5',
                'sha512': '24dbb6cb56757a621fb8e6a8c8733f1cfc3c77bd23ac325e672eaaf856eac602307541ac434f598afb62448e90b3608344cfeb2e64778d3f7024bc69f5bb46ef',
                'sha3-256': '8f33c358764548766d12885d06aea06d00469b2828cefb516b8f5aedc2826352'
            })
        ], any_order=True)
