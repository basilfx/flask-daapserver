from daapserver import responses

import cStringIO

__all__ = ["LocalFileProvider", "Provider", "Session"]

class Session(object):
    __slots__ = ["revision"]

    def __init__(self):
        self.revision = 1


class Provider(object):

    session_class = Session

    supports_artwork = False

    supports_persistent_id = False

    def __init__(self):
        """
        """

        self.server = None
        self.sessions = {}
        self.session_counter = 0

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
            # Increment revision, but never decrement.
            session.revision = max(session.revision, revision)
            self.check_sessions()

            # Wait for next revision
            next_revision = self.wait_for_update()
        else:
            next_revision = min(self.server.manager.revision, revision + 1)

        return next_revision

    def check_sessions(self):
        lowest_revision = min([ session.revision for session in self.sessions.itervalues() ])

        if lowest_revision == self.server.manager.revision:
            self.server.manager.commit()

    def wait_for_update(self):
        """
        """

        raise NotImplemented("Needs to be overridden")

    def get_databases(self, session_id, revision, delta):
        """
        """

        session = self.sessions[session_id]

        if delta == 0:
            new = self.server.databases
            old = None
        else:
            new = self.server.get_revision(revision).databases
            old = self.server.get_revision(delta).databases

        return responses.databases(new, old)

    def get_containers(self, session_id, database_id, revision, delta):
        """
        """

        session = self.sessions[session_id]

        if delta == 0:
            new = self.server.databases[database_id].containers
            old = None
        else:
            new = self.server.get_revision(revision).databases[database_id].containers
            old = self.server.get_revision(delta).database[database_id].containers

        return responses.containers(new, old)

    def get_container_items(self, session_id, database_id, container_id, revision, delta):
        """
        """

        session = self.sessions[session_id]

        if delta == 0:
            new = self.server.databases[database_id].containers[container_id].container_items
            old = None
        else:
            new = self.server.get_revision(revision).databases[database_id].containers[container_id].container_items
            old = self.server.get_revision(delta).databases[database_id].containers[container_id].container_items

        return responses.container_items(new, old)

    def get_items(self, session_id, database_id, revision, delta):
        """
        """
        session = self.sessions[session_id]

        if delta == 0:
            new = self.server.databases[database_id].items
            old = None
        else:
            new = self.server.get_revision(revision).databases[database_id].items
            old = self.server.get_revision(delta).databases[database_id].items

        return responses.items(new, old)

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
            fp.seek(start)
            return fp, item.mimetype, item.file_size
        elif begin and end:
            fp.seek(begin)

            data = fp.read(end - begin)
            result = cStringIO.StringIO(data)

            return result, item.mimetype, item.file_size

    def get_artwork_data(self, session, item):
        fp = open(item.artwork, "rb+")

        return fp, None, None