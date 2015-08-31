from daapserver.utils import parse_byte_range, invoke_hooks

from datetime import datetime

import enum
import cStringIO
import gevent.lock
import gevent.event

__all__ = ("LocalFileProvider", "Provider", "Session", "State")


class State(enum.Enum):
    """
    Client session states.
    """

    connecting = 1
    connected = 2
    streaming = 3


class Session(object):
    """
    Represents a client session. The session records the user agent, remote
    address, client version and keeps track of the number of items and artworks
    requested.
    """

    __slots__ = (
        "revision", "since", "state", "remote_address", "user_agent",
        "client_version", "counters")

    def __init__(self):
        """
        Construct a new Session object.
        """

        self.revision = 0
        self.since = datetime.now()
        self.state = State.connecting

        self.remote_address = None
        self.user_agent = None
        self.client_version = None

        self.counters = {
            "items": 0,
            "items_unique": 0,
            "artworks": 0
        }

    def increment_counter(self, counter):
        """
        Increment a counter value by one.

        :param str counter: Name of the counter
        """

        self.counters[counter] += 1


class Provider(object):
    """
    Base provider implementation. A provider is responsible for serving the
    data to the client. This class should be subclassed.
    """

    # Class type to use for sessions
    session_class = Session

    # Whether to artwork is supported
    supports_artwork = False

    # Whether persistent IDs are supported
    supports_persistent_id = False

    def __init__(self):
        """
        Create a new Provider. This method should be invoked from the subclass.
        """

        self.revision = 1
        self.server = None
        self.sessions = {}
        self.session_counter = 0
        self.hooks = {
            "session_created": [],
            "session_destroyed": [],
            "updated": []
        }

        self.lock = gevent.lock.Semaphore()
        self.next_revision_available = gevent.event.Event()

    def create_session(self, user_agent, remote_address, client_version):
        """
        Create a new session.

        :param str user_agent: Client user agent
        :param str remote_addr: Remote address of client
        :param str client_version: Remote client version
        :return: The new session id
        :rtype: int
        """

        self.session_counter += 1
        self.sessions[self.session_counter] = session = self.session_class()

        # Set session properties
        session.user_agent = user_agent
        session.remote_address = remote_address
        session.client_version = client_version

        # Invoke hooks
        invoke_hooks(self.hooks, "session_created", self.session_counter)

        return self.session_counter

    def destroy_session(self, session_id):
        """
        Destroy an (existing) session.
        """

        try:
            del self.sessions[session_id]
        except KeyError:
            pass

        # Invoke hooks
        invoke_hooks(self.hooks, "session_destroyed", session_id)

    def get_next_revision(self, session_id, revision, delta):
        """
        Determine the next revision number for a given session id, revision
        and delta.

        In case the client is up-to-date, this method will block until the next
        revision is available.

        :param int session_id: Session identifier
        :param int revision: Client revision number
        :param int delta: Client revision delta (old client version number)
        :return: Next revision number
        :rtype: int
        """

        session = self.sessions[session_id]
        session.state = State.connected

        if delta == revision:
            # Increment revision. Never decrement.
            session.revision = max(session.revision, revision)

            # Wait for next revision to become ready.
            self.next_revision_available.wait()

        return self.revision

    def update(self):
        """
        Update this provider. Should be invoked when the server gets updated.

        This method will notify all clients that wait for
        `self.next_revision_available`.
        """

        with self.lock:
            # Increment revision and commit it.
            self.revision += 1
            self.server.commit(self.revision + 1)

            # Unblock all waiting clients.
            self.next_revision_available.set()
            self.next_revision_available.clear()

            # Check sessions to see which revision can be removed.
            if self.sessions:
                lowest_revision = min(
                    session.revision for session in self.sessions.itervalues())

                # Remove all old revision history
                if lowest_revision == self.revision:
                    self.server.clean(lowest_revision)

        # Invoke hooks
        invoke_hooks(self.hooks, "updated", self.revision)

    def get_databases(self, session_id, revision, delta):
        """
        """

        if delta == 0:
            new = self.server.databases
            old = None
        else:
            new = self.server.databases(revision)
            old = self.server.databases(delta)

        return new, old

    def get_containers(self, session_id, database_id, revision, delta):
        """
        """

        if delta == 0:
            new = self.server \
                      .databases[database_id] \
                      .containers
            old = None
        else:
            new = self.server \
                      .databases[database_id] \
                      .containers(revision)
            old = self.server \
                      .databases[database_id] \
                      .containers(delta)

        return new, old

    def get_container_items(self, session_id, database_id, container_id,
                            revision, delta):
        """
        """

        if delta == 0:
            new = self.server \
                      .databases[database_id] \
                      .containers[container_id] \
                      .container_items
            old = None
        else:
            new = self.server \
                      .databases[database_id] \
                      .containers[container_id] \
                      .container_items(revision)
            old = self.server \
                      .databases[database_id] \
                      .containers[container_id] \
                      .container_items(delta)

        return new, old

    def get_items(self, session_id, database_id, revision, delta):
        """
        """

        if delta == 0:
            new = self.server \
                      .databases[database_id] \
                      .items
            old = None
        else:
            new = self.server \
                      .databases[database_id] \
                      .items(revision)
            old = self.server \
                      .databases[database_id] \
                      .items(delta)

        return new, old

    def get_item(self, session_id, database_id, item_id, byte_range=None):
        """
        """

        def _inner(data):
            # Change state to streaming
            session.state = State.streaming

            try:
                # Yield data
                if isinstance(data, basestring):
                    yield data
                else:
                    for chunk in data:
                        yield chunk
            finally:
                # Change state back to connected, even if an exception is
                # raised.
                session.state = State.connected

        session = self.sessions[session_id]
        item = self.server.databases[database_id].items[item_id]

        # Increment counter for statistics. Make a distinction between requests
        # with a byte range (play-pause) and ones without.
        session.increment_counter("items")

        if byte_range is None:
            session.increment_counter("items_unique")

        data, mimetype, size = self.get_item_data(session, item, byte_range)

        return _inner(data), mimetype, size

    def get_artwork(self, session_id, database_id, item_id):
        """
        """

        session = self.sessions[session_id]
        item = self.server.databases[database_id].items[item_id]

        # Increment counter for statistics
        session.increment_counter("artworks")

        return self.get_artwork_data(session, item)

    def get_item_data(self, session, item, byte_range=None):
        """
        Fetch the requested item. The result can be an iterator, file
        descriptor, or just raw bytes. Optionally, a begin and/or end range can
        be specified.

        The result should be an tuple, of the form (data, mimetype, size). The
        data can be an iterator, file descriptor or raw bytes. In case a range
        is requested, add a fourth tuple item, length. The length should be the
        size of the requested data that is being returned.

        Note: this method requires `Provider.supports_artwork = True`

        :param Session session: Client session
        :param Item item: Requested item.
        :param tuple byte_range: Optional byte range to return a part of the
                                 file.
        :return: File descriptor, iterator or raw bytes.
        """

        raise NotImplementedError("Needs to be overridden.")

    def get_artwork_data(self, session, item):
        """
        Fetch artwork for the requested item.

        The result should be an tuple, of the form (data, mimetype, size). The
        data can be an iterator, file descriptor or raw bytes.

        Note: this method requires `Provider.supports_artwork = True`

        :param Session session: Client session
        :param Item item: Requested item.
        :return: File descriptor, iterator or raw bytes.
        """

        raise NotImplementedError("Needs to be overridden.")


class LocalFileProvider(Provider):
    """
    Tiny implementation of a local file provider. Streams items and data from
    disk.
    """

    supports_artwork = True

    def get_item_data(self, session, item, byte_range=None):
        """
        Return a file pointer to the item file. Assumes `item.file_name` points
        to the file on disk.
        """

        # Parse byte range
        if byte_range is not None:
            begin, end = parse_byte_range(byte_range, max_byte=item.file_size)
        else:
            begin, end = 0, item.file_size

        # Open the file
        fp = open(item.file_name, "rb+")

        if not begin:
            return fp, item.file_type, item.file_size
        elif begin and not end:
            fp.seek(begin)
            return fp, item.file_type, item.file_size
        elif begin and end:
            fp.seek(begin)

            data = fp.read(end - begin)
            result = cStringIO.StringIO(data)

            return result, item.file_type, item.file_size

    def get_artwork_data(self, session, item):
        """
        Return a file pointer to the artwork file. Assumes `item.album_art`
        points to the file on disk.
        """

        fp = open(item.album_art, "rb+")

        return fp, None, None
