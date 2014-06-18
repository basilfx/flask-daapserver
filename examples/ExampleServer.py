from gevent.pywsgi import WSGIServer

from daapserver.provider import Server, Database, Container, Item, ContainerItem
from daapserver.structures import RevisionManager
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

        # It's important that `self.server' is set, as it is used by the rest of
        # the super class as an entry point.
        self.manager = manager = RevisionManager()
        self.server = server = Server(manager)

        # Add some fake data
        database = Database(manager, id=1, name="Library")
        server.add_database(database)

        container_one = Container(manager, id=1, name="My Music", is_base=True)
        container_two = Container(manager, id=2, name="Cool Music", parent=container_one)
        database.add_container(container_one, container_two)

        track_one = Item(manager, id=1, artist="Tenacious D", album="The Pick of Destiny", name="The Metal", track=15, duration=166000, year=2006, genre="Rock", file_suffix="mp3", file_type="audio/mp3")
        track_two = Item(manager, id=2, artist="Fait No More", album="The Real Thing", name="Epic", track=2, duration=291000,  year=1989, genre="Rock", file_suffix="mp3", file_type="audio/mp3")
        database.add_item(track_one, track_two)

        container_item_one_a = ContainerItem(manager, id=1, item=track_one)
        container_item_one_b = ContainerItem(manager, id=2, item=track_two)
        container_item_two_a = ContainerItem(manager, id=3, item=track_one, order=1)
        container_item_two_b = ContainerItem(manager, id=4, item=track_two, order=2)
        container_item_two_c = ContainerItem(manager, id=5, item=track_one, order=3)
        container_one.add_container_item(container_item_one_a, container_item_one_b)
        container_two.add_container_item(container_item_two_a, container_item_two_b, container_item_two_c)

    def wait_for_update(self):
        # In a real server, this should block until an update, and return the
        # next revision number.
        while True:
            gevent.sleep(1)

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplemented("Not supported for this example")

def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Create provider
    example_provider = ExampleProvider()

    # Register Zeroconf
    port = 3688 # Normally, DAAP runs at 3689, but this could conflict with iTunes

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