from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import DaapServer, provider

import sys
import copy
import gevent
import random
import logging

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

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a
        # database that hasn't been added to a server.
        database = Database(id=1, name="Library")
        server.databases.add(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        database.containers.add(container_one)

        # Spawn task do random things
        gevent.spawn(self.do_random_things)

        # Inform provider that the structure is ready.
        self.update()

    def do_random_things(self):
        database = self.server.databases[1]
        counter = 1

        while True:
            # Decide what to do
            if not database.items:
                choice = "add"
            else:
                # More chance on an adding items.
                choice = random.choice(["add", "add", "update", "remove"])

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
                    "%d.", item.id, len(database.items), self.revision)
            elif choice == "update":
                item = random.choice(database.items.values())
                container_item = database.containers[1] \
                                         .container_items[item.id]

                # Copy the items. This step is optional if you don't care
                # if older revision will all have the same data.
                item = copy.copy(item)
                container_item = copy.copy(container_item)

                # Update some properties.
                item.duration += 1000 * 60  # One minute

                database.containers[1] \
                        .container_items \
                        .add(container_item)
                database.items.add(item)
                logger.info(
                    "Item %d updated, %d items in container. Revision is "
                    "%d.", item.id, len(database.items), self.revision)
            elif choice == "remove":
                item = random.choice(database.items.values())
                container_item = database.containers[1] \
                                         .container_items[item.id]

                database.containers[1] \
                        .container_items \
                        .remove(container_item)
                database.items.remove(item)
                logger.info(
                    "Item %d removed, %d items in container. Revision is "
                    "%d.", item.id, len(database.items), self.revision)

            # The server and database have to be re-added so they are
            # marked as updated.
            database.containers.add(database.containers[1])
            self.server.databases.add(database)

            # Update the provider. This will unblock waiting clients.
            self.update()

            # Verify the change by computing the difference. This has nothing
            # to do with this example, except that it checks what happens is
            # correct.
            if choice in ["add", "update"]:
                assert list(database.items(self.revision).updated(
                    database.items(self.revision - 1))) == [item.id]
            elif choice == "remove":
                assert list(database.items(self.revision).removed(
                    database.items(self.revision - 1))) == [item.id]

            # Wait until next operation
            gevent.sleep(5.0)

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplementedError("Not supported in this example.")


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Create a server
    server = DaapServer(
        provider=RevisionProvider(),
        port=3688,
        debug=True)

    # Start a server and wait until CTRL + C is pressed.
    server.serve_forever()

# E.g. `python RevisionServer.py'
if __name__ == "__main__":
    sys.exit(main())
