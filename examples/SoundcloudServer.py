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


class RemoteItem(Item):
    """
    A standard Item does not have a field for item URL and artwork URL. This
    class extends Item by adding the fields. Note that `__slots__` is used for
    memory efficiency.
    """

    __slots__ = Item.__slots__ + ("file_url", "album_art_url")


class SoundcloudProvider(provider.LocalFileProvider):
    """
    Provide a quick-and-dirty in-memory content provider that uses Soundcloud
    as backend for providing data.

    This provider is not efficient, as it will download the file before use.
    Long tracks take some time before they actually start playing. Furthermore,
    this provider does not cleanup files after server exits.
    """

    def __init__(self, client_id, usernames):
        super(SoundcloudProvider, self,).__init__()

        # It's important that `self.server' is initialized, since it is used
        # throughout the class.
        self.server = server = Server(name="DAAPServer")

        # Add example data to the library. Note that everything should be added
        # in the right order. For instance, you cannot add an item to a
        # database that has not been added to a server yet.
        self.database = database = Database(id=1, name="Soundcloud Library")
        server.databases.add(database)

        self.container = container = Container(
            id=1, name="My Music", is_base=True)
        database.containers.add(container)

        # Prepare Soundcloud connection.
        self.temp_directory = tempfile.mkdtemp()
        self.client = soundcloud.Client(client_id=client_id)

        # Fetch tracks, asynchronous.
        gevent.spawn(self.get_tracks, usernames)

        # Inform provider that the structure is ready.
        self.update()

    def get_tracks(self, usernames):
        logger.info("Fetching tracks for usernames: %s", usernames)

        for username in usernames:
            logger.info("Fetching tracks for user '%s'", username)

            try:
                tracks = self.client.get("/users/%s/tracks" % username)
                logger.info(
                    "Found %d tracks for user '%s'.", len(tracks), username)
            except:
                logger.warning("Failed to get tracks for user '%s'", username)
                continue

            for index, track in enumerate(tracks):
                track = track.obj

                item = RemoteItem(
                    id=track["id"], artist=track["user"].get("username"),
                    name=track.get("title"), duration=track.get("duration"),
                    file_type="audio/mp3", file_suffix="mp3",
                    file_url="/tracks/%d/stream" % track["id"],
                    album_art_url=track["user"].get("avatar_url"),
                    album_art=True)
                container_item = ContainerItem(
                    id=len(self.container.container_items) + 1,
                    container_id=self.container.id,
                    item_id=item.id)

                # Add item to database
                self.database.items.add(item)
                self.container.container_items.add(container_item)

            # The server and database have to be re-added so they are marked as
            # updated.
            self.server.databases.add(self.database)
            self.database.containers.add(self.container)

            # Inform provider of new tracks.
            self.update()

    def get_item_data(self, session, item, byte_range=None):
        item.file_name = os.path.join(self.temp_directory, "%s.mp3" % item.id)
        file_size = download_file(
            self.client.get(item.file_url, allow_redirects=False).location,
            item.file_name)

        if file_size is not None:
            item.file_size = file_size

        # Stream actual item file from disk.
        return super(SoundcloudProvider, self).get_item_data(
            session, item, byte_range)

    def get_artwork_data(self, session, item):
        item.album_art = os.path.join(self.temp_directory, "%s.jpg" % item.id)

        # Replacing https:// is just a workaround SSL issues with OpenSSL and
        # requests problems.
        download_file(
            item.album_art_url.replace("https://", "http://"), item.album_art)

        # Stream actual artwork file from disk.
        return super(SoundcloudProvider, self).get_artwork_data(session, item)


def download_file(url, file_name):
    """
    Helper for downloading a remote file to disk.
    """

    logger.info("Downloading URL: %s", url)
    file_size = 0

    if not os.path.isfile(file_name):
        response = requests.get(url, stream=True)

        with open(file_name, "wb") as fp:
            if not response.ok:
                raise Exception("Download exception. Will fail.")

            for block in response.iter_content(1024):
                if not block:
                    break

                fp.write(block)
                file_size += len(block)

        logger.info("Download finished, size is %d bytes.", file_size)

    return file_size


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # Check arguments.
    if len(sys.argv) < 3:
        sys.stdout.write(
            "%s: <client_id> <user_1> .. <user_n>\n" % sys.argv[0])
        return 1

    # Create a server.
    server = DaapServer(
        provider=SoundcloudProvider(sys.argv[1], sys.argv[2:]),
        port=3688,
        debug=True)

    # Start a server and wait until CTRL + C is pressed.
    server.serve_forever()

# E.g. `python SoundcloudServer.py <client_id> <user_1> .. <user_n>'
if __name__ == "__main__":
    sys.exit(main())
