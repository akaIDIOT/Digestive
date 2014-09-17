from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, wait
from math import log

from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA512
from digestive.io import Source


_sizes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']


def file_size(size):
    order = int(log(size, 2) // 10) if size else 0
    if order >= len(_sizes):
        # exceeding ludicrous file sizes, default to bytes
        return '{} bytes'.format(size)
    return '{:.4g} {}'.format(size / (1 << (order * 10)), _sizes[order])


def parse_arguments(arguments=None):
    parser = ArgumentParser(description='run multiple digests on files')
    # hash digest sinks
    parser.add_argument('-m', '--md5', action='append_const', dest='sinks', const=MD5,
                        help='calculate MD5 hash')
    parser.add_argument('-1', '--sha1', action='append_const', dest='sinks', const=SHA1,
                        help='calculate SHA-1 hash')
    parser.add_argument('-2', '--sha256', action='append_const', dest='sinks', const=SHA256,
                        help='calculate SHA-256 hash')
    parser.add_argument('-5', '--sha512', action='append_const', dest='sinks', const=SHA512,
                        help='calculate SHA-512 hash')
    # convenience switch to include all hashes
    parser.add_argument('--hashes', action='store_const', dest='sinks', const=[MD5, SHA1, SHA256, SHA512],
                        help='calculate MD5, SHA-1, SHA-256 and SHA-512 hashes (equivalent to -m125)')
    # entropy sink
    parser.add_argument('-e', '--entropy', action='append_const', dest='sinks', const=Entropy,
                        help='calculate binary entropy')
    # misc options
    parser.add_argument('-j', '--jobs', type=int, metavar='JOBS',
                        help='use up to %(metavar)s threads to process digests (defaults to the number of digests)')
    # TODO: -b, --block-size (with support suffixes like M, Ki, likely all mapping to binary)
    # TODO: -t, --time
    # TODO: -p, --progress
    # TODO: refuse --progress when outputting to a dumb terminal
    # TODO: -r, --recursive
    # positional arguments: sources
    parser.add_argument('sources', metavar='FILE', nargs='+',
                        help='input files')

    arguments = parser.parse_args(arguments)
    process_arguments(arguments, parser)

    return arguments


def process_arguments(arguments, parser):
    if not arguments.sinks:
        parser.error('at least one sink is required')

    arguments.jobs = arguments.jobs if arguments.jobs else len(arguments.sinks)


def process_source(executor, source, sinks, block_size=1 << 20):
    generator = source.blocks(block_size)
    block = next(generator, False)
    while block:
        futures = [executor.submit(sink.update, block) for sink in sinks]
        block = next(generator, False)
        wait(futures)


def main(arguments=None):
    arguments = parse_arguments(arguments)

    with ThreadPoolExecutor(arguments.jobs) as executor:
        for file in arguments.sources:
            with Source(file) as source:
                # instantiate sinks from requested types
                sinks = [sink() for sink in arguments.sinks]
                print('{} ({})'.format(file, file_size(len(source))))

                process_source(executor, source, sinks)

                for sink in sinks:
                    print('  {:<12} {}'.format(sink.name, sink.digest()))
