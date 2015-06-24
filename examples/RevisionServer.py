from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import DaapServer, provider

import sys
import logging
import gevent
import gevent.event
import gevent.lock
import random

# Logger instance
logger = logging.getLogger(__name__)


class RevisionProvider(provider.Provider):
    """
    Provider that will randomly add or delete items, to show the revisioning
    system.
    """

    def __init__(self):
        super(RevisionProvider, self,).__init__()

        # It's important that `self.server' is initialized, since it is used
        # throughout the class.
        self.server = server = Server(name="DAAPServer")
        self.lock = gevent.lock.Semaphore()
        self.ready = gevent.event.Event()

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a
        # database that hasn't been added to a server.
        database = Database(id=1, name="Library")
        server.databases.add(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        database.containers.add(container_one)

        # Commit initial revision
        server.commit()

        # Spawn task do random things
        gevent.spawn(self.do_random_things)

    def do_random_things(self):
        database = self.server.databases[1]
        counter = 1

        while True:
            with self.lock:
                # Decide what to do
                choice = random.choice(["add", "add", "remove"])

                if choice == "add":
                    item = Item(
                        id=counter, artist="SubDaap", album="RevisionServer",
                        name="Item %d" % counter, duration=counter)
                    container_item = ContainerItem(id=counter, item_id=item.id)
                    counter += 1

                    database.items.add(item)
                    database.containers[1].container_items.add(container_item)
                    logger.info(
                        "Item %d added, %d items in container. Revision is "
                        "%d." % (
                            item.id, len(database.items),
                            self.server.revision))
                elif choice == "remove":
                    if len(database.items) == 0:
                        continue

                    item = random.choice(database.items.values())
                    container_item = database.containers[1] \
                                             .container_items[item.id]

                    database.containers[1] \
                            .container_items \
                            .remove(container_item)
                    database.items.remove(item)
                    logger.info(
                        "Item %d removed, %d items in container. Revision is "
                        "%d." % (
                            item.id, len(database.items),
                            self.server.revision))

                # Re-add the database, so it is marked as edited.
                database.containers.add(database.containers[1])
                self.server.databases.add(database)

            # Commit the changes.
            self.server.commit()

            # Verify the change by computing the difference.
            if choice == "add":
                assert list(database.items(self.server.revision).updated(
                    database.items(self.server.revision - 1))) == [item.id]
            elif choice == "remove":
                assert list(database.items(self.server.revision).removed(
                    database.items(self.server.revision - 1))) == [item.id]

            # Unblock waiting clients. This will update the clients.
            self.ready.set()
            self.ready.clear()

            # Wait until next operation
            gevent.sleep(5.0)

    def wait_for_update(self):
        # Wait for the next revision update
        self.ready.wait()

        # Return the revision number
        return self.server.revision

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplementedError("Not supported in this example.")


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Create server
    server = DaapServer(
        provider=RevisionProvider(),
        port=3688,
        debug=True)

    # Start a server and wait
    server.serve_forever()

# E.g. `python ExampleServer.py'
if __name__ == "__main__":
    sys.exit(main())
