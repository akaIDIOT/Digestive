from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime, timezone
from math import log
from os import path, walk
import re
import sys
import time

import yaml

import digestive
from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA3256, SHA3512, SHA512
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
    :raises TypeError: on unrecognized input.
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
    parser.add_argument('-3', '--sha3-256', action='append_const', dest='sinks', const=SHA3256,
                        help='calculate SHA3-256 hash')
    parser.add_argument('--sha3-512', action='append_const', dest='sinks', const=SHA3512,
                        help='calculate SHA3-512 hash')

    hashes = [MD5, SHA1, SHA256, SHA512, SHA3256]
    # convenience switch to include all hashes
    parser.add_argument('--hashes', action='store_const', dest='sinks', const=hashes,
                        help='calculate MD5, SHA-1, SHA-256, SHA-512 and SHA3-256 hashes (equivalent to -m1253)')
    # entropy sink
    parser.add_argument('-e', '--entropy', action='append_const', dest='sinks', const=Entropy,
                        help='calculate binary entropy')
    # misc options
    parser.add_argument('-j', '--jobs', type=int, metavar='JOBS',
                        help='use up to %(metavar)s threads to process digests (defaults to the number of digests)')
    parser.add_argument('-b', '--block-size', type=num_bytes, metavar='BYTES', default='1M',
                        help='read data in chunks of %(metavar)s at a time (defaults to 1M)')
    parser.add_argument('-p', '--progress', choices=('bytes', 'speed'), default='bytes',
                        help='show progress information (defaults to bytes)')
    parser.add_argument('-P', '--no-progress', action='store_false', dest='progress',
                        help='disable progress output (always disabled for redirected output)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='process sources recursively')
    parser.add_argument('-o', '--output',
                        help='write yaml-encoded output to file')
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
    """
    if not arguments.sinks:
        parser.error('at least one sink is required')

    arguments.jobs = arguments.jobs if arguments.jobs else len(arguments.sinks)


def output_to_file(output):
    """
    Collector of dicts to be written to output file as explicit YAML
    documents.

    :param output: The file name to write to (or None).
    :yield: Nothing, a collecting generator.
    """
    if output:
        # create a generator within a text-io context manager for output
        with open(output, 'w') as stream:
            while True:
                # receive source name and sink results
                value = yield
                # dump value to output, creating an explicit document start
                yaml.safe_dump(value, stream=stream, explicit_start=True, sort_keys=False)
    else:
        while True:
            # do nothing with any value received
            _ = yield  # variable _ is assigned to explicitly to make clear this is a collecting yield


def process_source(executor, source, sinks, block_size=1 << 20, progress=None):
    """
    Processes a data source, feeding chunks of at most block_size to each sink in parallel.

    :param executor: The executor to submit execution jobs to.
    :param source: The data source to read from.
    :param sinks: The sink instances to process data chunks with.
    :param block_size: The maximum chunk size to read.
    :param progress: a progress indicator, called with ``set(total_size)`` after each block has been processed
    :return: The total number of bytes read.
    """
    total_size = 0
    generator = source.blocks(block_size)
    block = next(generator, False)
    while block:
        total_size += len(block)
        futures = [executor.submit(sink.process, block) for sink in sinks]
        block = next(generator, False)
        wait(futures)
        if progress:
            progress.set(total_size)

    return total_size


def files(sources, recurse=False, followlinks=False):
    """
    Generates paths to files.

    :param sources: The base sources passed as arguments.
    :param recurse: Whether to recurse into directories.
    :param followlinks: Whether to follow symbolic links.
    :yield: Sources based on the provided arguments.
    """
    if recurse:
        for source in sources:
            # use walk to recurse into each source…
            for base, _, names in walk(source, followlinks=followlinks):
                # …and yield all the files within them
                # TODO: some intelligence might be nice here, like removing .E02 when .E01 is found
                yield from (path.join(base, name) for name in names)
    else:
        # simply use sources
        yield from sources


class Progress:
    types = {
        # show progress as total bytes processed
        'bytes': lambda processed, elapsed: file_size(processed,
                                                      template='{value:>8.3f} {unit}'),
        # show progress as bytes processed per second (use arbitrary value to avoid division by zero)
        'speed': lambda processed, elapsed: file_size(processed / (elapsed or 1.0),
                                                      template='{value:>8.3f} {unit}/s'),
    }

    def __init__(self, source, progress='bytes'):
        self.value = 0
        self.started = time.monotonic()
        self.end = len(source)
        self.progress = self.types[progress]

    def __enter__(self):
        return self

    def set(self, num):
        self.value = num
        if self.end:
            # progress only makes sense if end > 0
            self.print_progress()

    def print_progress(self):
        # use terminal escape to clear line and \r return cursor to start of line, followed by actual progress info
        print('\033[2K\r  {percent:>4.0%} [{bar:<20}] ({value})'.format(
            percent=(self.value / self.end),
            bar=('»' * int((20 * self.value / self.end))),
            value=self.progress(processed=self.value, elapsed=time.monotonic() - self.started),
        ), end='')

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('\033[2K\r', end='')


def main(arguments=None):
    """
    Runs digestive.

    :param arguments: Commandline arguments, passed to parse_arguments.
    """
    arguments = parse_arguments(arguments)
    # create the output generator
    output = output_to_file(arguments.output)
    # initialize output (moves it to the first occurrence of yield)
    next(output)
    info = {'digestive': str(digestive.__version__),
            'started': datetime.now(tz=timezone.utc)}
    output.send(info)

    with ThreadPoolExecutor(arguments.jobs) as executor:
        for file in files(arguments.sources, arguments.recursive):
            with Source(file) as source:
                # instantiate sinks from requested types
                sinks = [sink() for sink in arguments.sinks]
                # flush initial status line to force it to show in something like | less
                print('{} ({})'.format(source, file_size(len(source))), flush=True)

                if arguments.progress and sys.stdout.isatty():
                    with Progress(source, arguments.progress) as progress:
                        size = process_source(executor, source, sinks, arguments.block_size, progress=progress)
                else:
                    size = process_source(executor, source, sinks, arguments.block_size)

                results = {sink.name: sink.result() for sink in sinks}
                for name, result in results.items():
                    if result is not None:  # exclude Nones from results
                        print('  {:<12} {}'.format(name, result))

                # create meta data leader
                # TODO: using kwargs here would be nice, but that destroys order :( (see PEP-468)
                info = {'source': file,
                        'size': size,
                        'completed': datetime.now(tz=timezone.utc)}
                # add results
                info.update(results)
                # send info to the output collector
                output.send(info)

    # close the output collector, which in turn closes the output stream
    output.close()


if __name__ == '__main__':
    main()
