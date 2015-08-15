from six.moves import xrange

from daapserver.revision import RevisionStore

import argparse
import sys


def parse_arguments():
    """
    Parse commandline arguments.
    """

    parser = argparse.ArgumentParser()

    # Add options
    parser.add_argument(
        "-n", "--number", action="store", default=1000000, type=int,
        help="number of items")
    parser.add_argument(
        "-p", "--pause", action="store_true", help="pause after execution")

    # Parse command line
    return parser.parse_args(), parser


def main():
    """
    Run a benchmark for N items. If N is not specified, take 1,000,000 for N.
    """

    # Parse arguments and configure application instance.
    arguments, parser = parse_arguments()

    # Start iterating
    store = RevisionStore()
    sys.stdout.write("Iterating over %d items.\n" % arguments.number)

    for i in xrange(arguments.number):
        key = chr(65 + (i % 26))
        value = [key * (i % 26), key * (i % 13), key * (i % 5)]

        store.add(key, value)

    # Wait for an enter
    if arguments.pause:
        sys.stdout.write("Done!")
        sys.stdin.readline()

# E.g. `python benchmark_store.py [-n <items>] [-p]`
if __name__ == "__main__":
    sys.exit(main())
