from gevent.pywsgi import WSGIServer

from daapserver.provider import Server, Database, Container, Item
from daapserver import zeroconf, provider, create_daap_server

import sys
import random
import logging
import libsonic
import gevent
import os

# Logger instance
logger = logging.getLogger(__name__)

class ExampleProvider(provider.Provider):
    """
    Provide a quick-and-dirty in-memory content provider. This provider does not
    stream any data, or update any clients.
    """

    def __init__(self):
        super(ExampleProvider, self,).__init__()

        self.server = server = Server()

        database = Database(id=1, name="Library")
        server.add_database(database)

        container_one = Container(id=1, name="My Music", is_base=True)
        container_two = Container(id=2, name="Cool Music", parent=container_one)
        database.add_container(container_one)
        database.add_container(container_two)

        track_one = track_one = Item(id=1, artist="Tenacious D", title="The Metal", track=15, duration=166000, type="mp3", year=2006, genre="Rock", mimetype="audio/mp3")
        track_two = track_two = Item(id=2, artist="Fait No More", title="Epic", track=2, duration=291000, type="mp3", year=1989, genre="Rock", mimetype="audio/mp3")

        database.add_item(track_one)
        database.add_item(track_two)

        container_one.add_item(track_one)
        container_one.add_item(track_two)
        container_two.add_item(track_two)

    def wait_for_update(self):
        # In a real server, this should block until an update, and return the
        # next revision number.
        while True:
            gevent.sleep(1)

    def get_item_data(self, *args, **kwargs):
        # Normally, you would provide a file pointer or raw bytes here.
        raise NotImplemented

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