from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, wait
from math import log
from os import path
import re
import sys

from digestive.entropy import Entropy
from digestive.ewf import EWFSource, supported_exts as ewf_supported_formats
from digestive.hash import MD5, SHA1, SHA256, SHA512
from digestive.io import Source


# binary suffixes for byte sizes
_sizes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB']
# the corresponding suffixes
_suffixes = [size[0].lower() for size in _sizes]
# multipliers for byte size arguments taken from _suffixes
_multipliers = {suffix: 1 << (i * 10) for i, suffix in enumerate(_suffixes)}


def file_size(size, template='{value:.4g} {unit}'):
    """
    Converts a byte size into a human-readable format using binary suffixes.

    :param size: The value to be formatted.
    :param template: A format string with two parameters: value and unit.
    :return: A human-readable file size.
    """
    order = int(log(size, 2) // 10) if size else 0
    if order >= len(_sizes):
        # exceeding ludicrous file sizes, default to bytes
        return '{} bytes'.format(size)
    return template.format(value=size / (1 << (order * 10)), unit=_sizes[order])


def num_bytes(size):
    """
    Converts a human-readable byte size into an int, stripping an optional binary suffix.

    :param size: The size to be parsed.
    :return: An int.
    """
    match = re.match(r'(?P<size>\d+)(?P<suffix>[{}])?$'.format(''.join(_suffixes)), size, re.IGNORECASE)
    if match:
        # one optional group, no suffix is 'b' for bytes
        size, suffix = match.groups('b')
        return int(size) * _multipliers.get(suffix.lower())
    else:
        raise TypeError(size)


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
    parser.add_argument('-b', '--block-size', type=num_bytes, metavar='BYTES', default='1M',
                        help='read data in chunks of %(metavar)s at a time (defaults to 1M)')
    # TODO: specifying --format ewf on files that don't match supported exts will raise ValueError
    parser.add_argument('-f', '--format', choices=('auto', 'raw', 'ewf'), default='auto',
                        help='specify source format (defaults to auto)')
    # TODO: add choice (and implement) throughput / speed, eta
    parser.add_argument('-p', '--progress', choices=('bytes',), default='bytes',
                        help='show progress information (defaults to bytes)')
    parser.add_argument('-P', '--no-progress', action='store_false', dest='progress',
                        help='disable progress output (always disabled for piped output)')
    # TODO: -t, --time
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


def process_source(executor, source, sinks, block_size=1 << 20, progress=None):
    """
    Processes a data source, feeding chunks of at most block_size to each sink in parallel.

    :param executor: The executor to submit execution jobs to.
    :param source: The data source to read from.
    :param sinks: The sink instances to process data chunks with.
    :param block_size: The maximum chunk size to read.
    :param progress: An object to call add(int) on for every read block.
    """
    generator = source.blocks(block_size)
    block = next(generator, False)
    while block:
        if callable(progress):
            progress(len(block))
        futures = [executor.submit(sink.process, block) for sink in sinks]
        block = next(generator, False)
        wait(futures)


def get_source(file, source_type='auto'):
    if source_type == 'raw':
        return Source(file)
    elif source_type == 'ewf':
        return EWFSource(file)
    elif source_type == 'auto':
        basename, ext = path.splitext(file)
        source_type = 'ewf' if ext.lower() in ewf_supported_formats else 'raw'
        return get_source(file, source_type=source_type)
    else:
        raise ValueError('unknown source type: {}'.format(source_type))


def main(arguments=None):
    """
    Runs digestive.

    :param arguments: Commandline arguments, passed to parse_arguments.
    """
    class Progress:
        """
        FIXME: I'm a bit of a hack...
        """

        def __init__(self, end):
            self.value = 0
            self.end = end

        def __call__(self, amount):
            self.value += amount
            if self.end:
                # progress only makes sense if end > 0
                print_progress(self.value, self.end)

    def print_progress(current, end):
        # TODO: line not properly cleared if Entropy is first sink (result not wide enough)
        print('\r  {percent:>4.0%} [{bar:<20}] ({value})'.format(
            percent=(current / end),
            bar=('»' * int((20 * current / end))),  # TODO: will » work everywhere?
            value=file_size(current, '{value:>8.3f} {unit}')
        ), end='')

    arguments = parse_arguments(arguments)

    with ThreadPoolExecutor(arguments.jobs) as executor:
        # TODO: globs like tests/files/file.* includes both file.E01 and file.E02
        # TODO: only file.E01 will get treated as ewf, file.E02 should be removed from sources
        for file in arguments.sources:
            with get_source(file, arguments.format) as source:
                # instantiate sinks from requested types
                sinks = [sink() for sink in arguments.sinks]
                # flush initial status line to force it to show in something like | less
                print('{} ({})'.format(source, file_size(len(source))), flush=True)

                if arguments.progress and sys.stdout.isatty():
                    # stdout should support carriage returns, engage progress information!
                    process_source(executor, source, sinks, arguments.block_size, progress=Progress(end=len(source)))
                    # print next (result) line over progress information
                    print('\r', end='')
                else:
                    # omit progress altogether
                    process_source(executor, source, sinks, arguments.block_size)

                for sink in sinks:
                    print('  {:<12} {}'.format(sink.name, sink.digest()))


if __name__ == '__main__':
    main()
