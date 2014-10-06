from gevent.pywsgi import WSGIServer

from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import zeroconf, provider, create_daap_server

import sys
import logging
import gevent

# Logger instance
logger = logging.getLogger(__name__)

class ExampleProvider(provider.Provider):
    """
    Provide a quick-and-dirty in-memory content provider. This provider does not
    stream any data, or update any clients.
    """

    def __init__(self):
        super(ExampleProvider, self,).__init__()

        # It's important that `self.server' is initialized, since it is used
        # throughout the class.
        self.server = server = Server()

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a database
        # that hasn't been added to a server.
        database = Database(id=1, name="Library")
        server.databases.add(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        container_two = Container(id=2, name="Cool Music", parent=container_one)
        container_three = Container(id=3, name="Empty Playlist", parent=container_two)
        database.containers.add(container_one)
        database.containers.add(container_two)
        database.containers.add(container_three)

        item_one = Item(id=1, artist="Tenacious D", album="The Pick of Destiny", name="The Metal", track=15, duration=166000, year=2006, genre="Rock", file_suffix="mp3", file_type="audio/mp3")
        item_two = Item(id=2, artist="Fait No More", album="The Real Thing", name="Epic", track=2, duration=291000,  year=1989, genre="Rock", file_suffix="mp3", file_type="audio/mp3")
        database.items.add(item_one)
        database.items.add(item_two)

        container_item_one_a = ContainerItem(id=1, item=item_one)
        container_item_one_b = ContainerItem(id=2, item=item_two)
        container_item_two_a = ContainerItem(id=3, item=item_one, order=1)
        container_item_two_b = ContainerItem(id=4, item=item_two, order=2)
        container_item_two_c = ContainerItem(id=5, item=item_one, order=3)
        container_one.container_items.add(container_item_one_a)
        container_one.container_items.add(container_item_one_b)
        container_two.container_items.add(container_item_two_a)
        container_two.container_items.add(container_item_two_b)
        container_two.container_items.add(container_item_two_c)

        # Commit changes, so next updates will start new revision
        server.storage.commit()

    def wait_for_update(self):
        # In a real server, this should block until an update, and return the
        # next revision number.
        while True:
            gevent.sleep(1)

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplemented("Not supported for this example")

def main(port=3688):
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Create provider
    example_provider = ExampleProvider()

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