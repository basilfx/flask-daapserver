from gevent.pywsgi import WSGIServer

from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import zeroconf, provider, create_daap_server

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
        self.server = server = Server()
        self.lock = gevent.lock.Semaphore()

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a database
        # that hasn't been added to a server.
        database = Database(id=1, name="Library")
        server.databases.add(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        database.containers.add(container_one)

        # Server init ready
        server.storage.commit()

        # Event which synchronizes new revision
        self.ready = gevent.event.Event()

        # Spawn task do random things
        gevent.spawn(self.do_random_things)

    def do_random_things(self):
        database = self.server.databases[1]
        counter = 1

        while True:
            with self.lock:
                # Decide what to do
                if random.choice(["add", "add", "add", "del"]) == "add":
                    item = Item(id=counter, artist="SubDaap", album="RevisionServer", name="Item %d" % counter, duration=counter)
                    container_item = ContainerItem(id=counter, item=item)
                    counter += 1

                    # Add
                    database.items.add(item)
                    database.containers[1].container_items.add(container_item)
                    logger.info("Added item %d. %d in container." % (item.id, len(database.items)))
                else:
                    if len(database.items) == 0:
                        continue

                    item = random.choice(database.items.values())
                    container_item = database.containers[1].container_items[item.id]

                    # Remove
                    database.containers[1].container_items.remove(container_item)
                    database.items.remove(item)
                    logger.info("Removed item %d. %d in container left." % (item.id, len(database.items)))

                # Re-add the database, so it is marked as edited.
                database.containers.add(database.containers[1])
                self.server.databases.add(database)

            # Unblock waiting clients
            self.server.storage.commit()
            self.ready.set()
            self.ready.clear()

            # Wait until next operation
            gevent.sleep(5.0)

    def wait_for_update(self):
        # In a real server, this should block until an update, and return the
        # next revision number.
        self.ready.wait()

        # Return the revision number
        return self.server.storage.revision

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplemented("Not supported for this example")

def main(port=3688):
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Create provider
    example_provider = RevisionProvider()

    # Register Zeroconf
    service = zeroconf.Zeroconf("DaapServer", port, stype="_daap._tcp")
    service.publish()

    # Start a server and wait
    application = create_daap_server(example_provider, server_name="DaapServer")
    server = WSGIServer(("", port), application=application)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    # Unpublish
    service.unpublish()

# E.g. `python ExampleServer.py'
if __name__ == "__main__":
    sys.exit(main())