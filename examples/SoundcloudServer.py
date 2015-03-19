from daapserver.models import Server, Database, Item, Container, ContainerItem
from daapserver import DaapServer, provider

import os
import sys
import gevent
import logging
import tempfile
import requests
import soundcloud

# Logger instance
logger = logging.getLogger(__name__)


class SoundcloudProvider(provider.LocalFileProvider):
    """
    Provide a quick-and-dirty in-memory content provider that uses Soundcloud
    to as backend.
    """

    def __init__(self, client_id, user_id):
        super(SoundcloudProvider, self,).__init__()

        # It's important that `self.server' is initialized, since it is used
        # throughout the class.
        self.server = server = Server(id=1)

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a
        # database that hasn't been added to a server.
        database = Database(id=1, name="Soundcloud Library")
        server.databases.add(database)

        base_container = Container(
            id=1, name="My Music", is_base=True)
        database.containers.add(base_container)

        self.temp_directory = tempfile.mkdtemp()
        self.client = soundcloud.Client(client_id=client_id)
        tracks = self.client.get("/users/%s/tracks" % user_id)

        for index, track in enumerate(tracks):
            track = track.obj
            item = Item(
                id=track["id"], artist=track["user"].get("username"),
                name=track.get("title"), duration=track.get("duration"),
                file_type="audio/mp3", file_suffix="mp3")
            container_item = ContainerItem(id=index + 1, item_id=item.id)

            # Add to database
            database.items.add(item)
            base_container.container_items.add(container_item)

        logger.info("Found %d tracks for user id %s", len(tracks), user_id)

        # Commit changes, so next updates will start new revision
        server.storage.commit()

    def wait_for_update(self):
        # In a real server, this should block until an update, and return the
        # next revision number.
        while True:
            gevent.sleep(1)

    def get_item_data(self, session, item, byte_range=None):
        item.file_name = os.path.join(self.temp_directory, "%s.mp3" % item.id)

        if not os.path.isfile(item.file_name):
            url = self.client.get(
                "/tracks/%d/stream" % item.id, allow_redirects=False)
            item.file_size = 0

            with open(item.file_name, "wb") as fp:
                response = requests.get(url.location, stream=True)

                if not response.ok:
                    raise Exception("Download exception. Will fail")

                for block in response.iter_content(1024):
                    if not block:
                        break

                    fp.write(block)
                    item.file_size += len(block)

            logger.info(
                "Downloaded track id %s of size %d", item.id, item.file_size)

        # Stream actual file
        return super(SoundcloudProvider, self).get_item_data(
            session, item, byte_range)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Check arguments
    if len(sys.argv) != 3:
        sys.stdout.write("%s: <client_id> <user_id>\n" % sys.argv[0])
        return 1

    # Create server
    server = DaapServer(
        provider=SoundcloudProvider(sys.argv[1], sys.argv[2]),
        server_name="DaapServer",
        port=3688,
        debug=True)

    # Start a server and wait
    server.serve_forever()

# E.g. `python SoundcloudServer.py <client_id> <user_id>'
if __name__ == "__main__":
    sys.exit(main())
