from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import provider

import gc
import sys
import time
import logging
import contextlib

try:
    import psutil
except ImportError:
    psutil = None
    sys.stderr.write("Memory usage info disabled. Install psutils first.\n")

# Logger instance
logger = logging.getLogger(__name__)


class BenchmarkProvider(provider.Provider):
    """
    Benchmarking provider. Adds N numbers of items to the database and the base
    container. The odd numbers are added to a second container, the even items
    are added to a third container.
    """

    def __init__(self):
        super(BenchmarkProvider, self,).__init__()

        # It's important that `self.server' is initialized, since it is used
        # throughout the class.
        self.server = server = Server(name="Benchmark Server")

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a
        # database that hasn't been added to a server.
        database = Database(id=1, name="Library")
        server.databases.add(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        container_two = Container(
            id=2, name="Even", parent_id=container_one.id)
        container_three = Container(
            id=3, name="Uneven", parent_id=container_one.id)
        database.containers.add(container_one)
        database.containers.add(container_two)
        database.containers.add(container_three)

        # Server initial commit
        server.commit()

    def benchmark(self, count):
        # Save references
        server = self.server
        database = server.databases[1]

        container_one = database.containers[1]
        container_two = database.containers[2]
        container_three = database.containers[3]

        # Execute `count' operations of addition
        for i in xrange(count):
            item = Item(
                id=i, artist="SubDaap", album="RevisionServer",
                name="Item %d" % i, duration=i, bitrate=320, year=2014)

            container_item_a = ContainerItem(id=i, item_id=item.id)
            container_item_b = ContainerItem(id=i, item_id=item.id)

            database.items.add(item)
            container_one.container_items.add(container_item_a)

            if i % 2 == 0:
                container_two.container_items.add(container_item_b)
            else:
                container_three.container_items.add(container_item_b)

        # Update server and database
        database.containers.add(container_one)
        database.containers.add(container_two)
        database.containers.add(container_three)

        server.databases.add(database)

        # Clean old revision history
        server.clean(server.revision)

        # Iterate over items
        x = database.items.values()

        a = container_one.container_items.values()
        b = container_two.container_items.values()
        c = container_three.container_items.values()

        return len(x) + len(a) + len(b) + len(c)


@contextlib.contextmanager
def measure(test, disable_gc):
    # Disable garbage collector
    if disable_gc:
        gc.disable()

    # Take start time
    start = time.time()

    # Execute test
    yield

    # Take end time
    end = time.time()

    # Measure memory, if psutil is installed and loaded.
    if psutil:
        memory = psutil.Process().memory_info()[0] / 1024 / 1024
    else:
        memory = 0.0

    # Report
    logger.info(
        "Test '%s' took %.04f seconds, memory usage is %.02f MB.",
        test, end - start, memory)

    # Wait for enter
    raw_input("Press enter to continue.")

    # Re-enable garbage collector
    if disable_gc:
        gc.enable()

    # Invoke a collect
    gc.collect()


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    for disable_gc in [True]:
        with measure("100 items", disable_gc):
            BenchmarkProvider().benchmark(100)

        with measure("1000 items", disable_gc):
            BenchmarkProvider().benchmark(1000)

        with measure("10000 items", disable_gc):
            BenchmarkProvider().benchmark(10000)

        with measure("50000 items", disable_gc):
            BenchmarkProvider().benchmark(50000)

        with measure("100000 items", disable_gc):
            BenchmarkProvider().benchmark(100000)

        with measure("500000 items", disable_gc):
            BenchmarkProvider().benchmark(500000)

    logger.info("Done!")

# E.g. `python benchmark.py'
if __name__ == "__main__":
    sys.exit(main())
