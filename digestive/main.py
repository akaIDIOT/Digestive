from argparse import ArgumentParser

from digestive.entropy import Entropy
from digestive.hash import MD5, SHA1, SHA256, SHA512


def parse_arguments(args=None):
    parser = ArgumentParser(args)
    # hash digest sinks
    parser.add_argument('-m', '--md5', action='append_const', dest='sinks', const=MD5)
    parser.add_argument('-1', '--sha1', action='append_const', dest='sinks', const=SHA1)
    parser.add_argument('-2', '--sha256', action='append_const', dest='sinks', const=SHA256)
    parser.add_argument('-5', '--sha512', action='append_const', dest='sinks', const=SHA512)
    # entropy sink
    parser.add_argument('-e', '--entropy', action='append_const', dest='sinks', const=Entropy)
    # misc options
    parser.add_argument('-j', '--jobs', type=int)
    # TODO: -t, --time
    # TODO: -p, --progress
    # TODO: refuse --progress when outputting to a dumb terminal
    # TODO: -r, --recursive
    # positional arguments: sources
    parser.add_argument('sources', metavar='FILE', nargs='+')

    args = parser.parse_args()
    process_args(args, parser)

    return args


def process_args(args, parser):
    if not args.sinks:
        parser.error('at least one sink is required')

    args.jobs = args.jobs if args.jobs else len(args.sinks)
