from six.moves import xrange

from daapserver.revision import RevisionStore

import sys


def main():
    """
    Run a benchmark for N items. If N is not specified, take 1,000,000 as N.
    """

    # Decide on the number of items
    try:
        items = int(sys.argv[1])
    except:
        items = 1000000

    sys.stdout.write("Iterating over %d items.\n" % items)

    # Start iterating
    store = RevisionStore()

    for i in xrange(items):
        key = chr(65 + (i % 26))
        value = [key * (i % 26), key * (i % 13), key * (i % 5)]

        store.add(key, value)

    # Wait for an enter
    sys.stdout.write("Done!")
    sys.stdin.readline()

# E.g. `python benchmark.py <items>`
if __name__ == "__main__":
    sys.exit(main())
