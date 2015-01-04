from datetime import datetime

import cStringIO

__all__ = ("LocalFileProvider", "Provider", "Session")


class DummyLock(object):
    def __enter__(self):
        pass

    def __exit__(self, typ, value, traceback):
        pass


class Session(object):
    __slots__ = ("revision", "since")

    def __init__(self):
        self.revision = 0
        self.since = datetime.now()


class Provider(object):

    # Class type to use for sessions
    session_class = Session

    # Whether to artwork is supported
    supports_artwork = False

    # Whether persistent IDs are supported
    supports_persistent_id = False

    def __init__(self):
        """
        """

        self.server = None
        self.sessions = {}
        self.session_counter = 0
        self.lock = DummyLock()

    def create_session(self):
        """
        """

        self.session_counter += 1
        self.sessions[self.session_counter] = self.session_class()

        return self.session_counter

    def destroy_session(self, session_id):
        """
        """

        try:
            del self.sessions[session_id]
        except KeyError:
            pass

    def get_revision(self, session_id, revision, delta):
        """
        """

        session = self.sessions[session_id]

        if delta == revision:
            # Increment revision. Never decrement.
            session.revision = max(session.revision, revision)

            # Check sessions.
            self.check_sessions()

            # Wait for next revision
            next_revision = self.wait_for_update()
        else:
            next_revision = self.server.storage.revision

        return next_revision

    def check_sessions(self):
        """
        """

        lowest_revision = min(
            session.revision for session in self.sessions.itervalues())

        # Remove all old revision history
        if lowest_revision == self.server.storage.revision:
            with self.lock:
                self.server.storage.clean(lowest_revision)

    def wait_for_update(self):
        """
        """

        raise NotImplemented("Needs to be overridden")

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
                      .databases(revision)[database_id] \
                      .containers(revision)
            old = self.server \
                      .databases(delta)[database_id] \
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
                      .databases(revision)[database_id] \
                      .containers(revision)[container_id] \
                      .container_items(revision)
            old = self.server \
                      .databases(delta)[database_id] \
                      .containers(delta)[container_id] \
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
                      .databases(revision)[database_id] \
                      .items(revision)
            old = self.server \
                      .databases(delta)[database_id] \
                      .items(delta)

        return new, old

    def get_item(self, session_id, database_id, item_id, byte_range=None):
        """
        """

        session = self.sessions[session_id]
        item = self.server.databases[database_id].items[item_id]

        return self.get_item_data(session, item, byte_range)

    def get_artwork(self, session_id, database_id, item_id):
        """
        """

        session = self.sessions[session_id]
        item = self.server.databases[database_id].items[item_id]

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

        Note: this method requires `Provider.supports_artwork = True'
        """

        raise NotImplemented("Needs to be overridden")

    def get_artwork_data(self, session, item):
        """
        Fetch artwork for the requested item.

        The result should be an tuple, of the form (data, mimetype, size). The
        data can be an iterator, file descriptor or raw bytes.

        Note: this method requires `Provider.supports_artwork = True'
        """

        raise NotImplemented("Needs to be overridden")


class LocalFileProvider(Provider):

    supports_artwork = True

    def get_item(self, session, item, byte_range=None):
        begin, end = byte_range if byte_range else 0, item.file_size
        fp = open(item.file_path, "rb+")

        if not begin:
            return fp, item.mimetype, item.file_size
        elif begin and not end:
            fp.seek(begin)
            return fp, item.mimetype, item.file_size
        elif begin and end:
            fp.seek(begin)

            data = fp.read(end - begin)
            result = cStringIO.StringIO(data)

            return result, item.mimetype, item.file_size

    def get_artwork_data(self, session, item):
        fp = open(item.artwork, "rb+")

        return fp, None, None
