from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, wait
from math import log

from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA512
from digestive.io import Source


_sizes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']


def file_size(size):
    """
    Converts a byte size into a human-readable format using binary prefixes.

    :param size: The value to be formatted.
    :return: A human-readable file size.
    """
    order = int(log(size, 2) // 10) if size else 0
    if order >= len(_sizes):
        # exceeding ludicrous file sizes, default to bytes
        return '{} bytes'.format(size)
    return '{:.4g} {}'.format(size / (1 << (order * 10)), _sizes[order])


def parse_arguments(arguments=None):
    """
    Parses commandline arguments defining both program options and input and output.

    :param arguments: The arguments to parse, or None. Arguments will be read from sys.argv if None.
    :return: An argparse.Namespace object.
    """
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
    """
    Post-processes parsed arguments.

    :param arguments: The arguments to be processed (an argparse.Namespace object).
    :param parser: The parser used to parse the arguments (used for error reporting).
    :return: The passed arguments, adjusted where needed.
    """
    if not arguments.sinks:
        parser.error('at least one sink is required')

    arguments.jobs = arguments.jobs if arguments.jobs else len(arguments.sinks)


def process_source(executor, source, sinks, block_size=1 << 20):
    """
    Processes a data source, feeding chunks of at most block_size to each sink in parallel.

    :param executor: The executor to submit execution jobs to.
    :param source: The data source to read from.
    :param sinks: The sink instances to process data chunks with.
    :param block_size: The maximum chunk size to read.
    """
    generator = source.blocks(block_size)
    block = next(generator, False)
    while block:
        futures = [executor.submit(sink.update, block) for sink in sinks]
        block = next(generator, False)
        wait(futures)


def main(arguments=None):
    """
    Runs digestive.

    :param arguments: Commandline arguments, passed to parse_arguments.
    """
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
