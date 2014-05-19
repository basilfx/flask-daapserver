from daapserver.structures import RevisionManager, RevisionDict
from daapserver import responses

from datetime import datetime

import cStringIO

class BaseObject(object):
    __slots__ = []

    __children__ = []
    __propagate__ = []

    def set_manager(self, manager):
        """
        Set the revision manager and propagate it to the attributes defined in
        `__propagate__' and `__childred___'.
        """

        for propagate in self.__propagate__:
            for item in getattr(self, propagate).get_revision().itervalues():
                item.manager = manager

        for child in self.__children__:
            getattr(self, child).manager = manager

    def get_manager(self):
        """
        Return the revision manager. Since every attribute defined in
        `__children__' has the same revision manager, return it from the first
        one.
        """

        return getattr(self, self.__children__[0]).manager

    manager = property(get_manager, set_manager)

    def get_revision(self, revision):
        """
        Return the state of this instance at a particular revision. This
        revision is propagated to the attributes defined in `__propagate__' and
        `__childred___', e.g. `self.get_revision(1).children' will be the same
        as `self.children.get_revision(1)'.
        """

        class _Proxy(object):
            def __init__(other):
                """
                Construct a new revision proxy.
                """

                for propagate in self.__propagate__:
                    items = getattr(self, propagate).get_revision(revision)
                    items.wrapper = lambda x: x.get_revision(revision)

                    setattr(other, propagate, items)

                for child in self.__children__:
                    if child not in self.__propagate__:
                        items = getattr(self, child).get_revision(revision)

                        setattr(other, child, items)

            def __getattr__(other, attr):
                """
                Proxy all attributes except the ones from defined in
                `__propagate__' and `__childred___'.
                """

                if attr in self.__propagate__ or attr in self.__children__:
                    return getattr(other, attr)
                else:
                    return getattr(self, attr)
        return _Proxy()

class Server(BaseObject):
    __slots__ = ["databases"]

    __children__ = ["databases"]
    __propagate__ = ["databases"]

    def __init__(self, **kwargs):
        """
        """

        self.databases = RevisionDict()

    def add_database(self, database):
        """
        """

        if database.server and database.server != self:
            raise ValueError("Database is already associated with another Server")

        if database.server is None:
            #self.manager.import_log(database.manager)

            database.manager = self.manager
            database.server = self

        self.databases[database.id] = database

    def delete_database(self, database):
        """
        """

        database.manager = RevisionManager()
        database.server = None

        del self.databases[database.id]

class Database(BaseObject):
    __slots__ = ["id", "persistent_id", "name", "items", "containers", "server", "checksum"]

    __children__ = ["items", "containers"]
    __propagate__ = ["containers"]

    def __init__(self, **kwargs):
        self.id = 1
        self.persistent_id = 1
        self.name = None
        self.server = None

        self.items = RevisionDict()
        self.containers = RevisionDict(self.items.manager)

        for attr, value in kwargs.iteritems():
            if attr in self.__slots__:
                setattr(self, attr, value)

    def __repr__(self):
        return "<Datebase(id=%d, name=%s)>" % (self.id, self.name)

    def add_item(self, item):
        """
        """

        if item.database  and item.database != self:
            raise ValueError("Item is already associated with another Database")

        if item.database is None:
            item.database = self

        self.items[item.id] = item

    def delete_item(self, item):
        """
        """

        item.database = None

        del self.items[item.id]

    def get_items(self, revision):
        pass


    def add_container(self, container):
        """
        """

        if container.database and container.database != self:
            raise ValueError("Container is already associated with another Database")

        if container.database is None:
            #self.revision_manager.import_log(container.revision_manager)

            container.manager = self.manager
            container.database = self

        self.containers[container.id] = container

    def delete_container(self, container):
        """
        """

        container.manager = RevisionManager()
        container.database = None

        del self.containers[container.id]

class Container(BaseObject):
    __slots__ = ["id", "persistent_id", "name", "items", "parent", "is_base", "is_smart", "database", "checksum"]

    __children__ = ["items"]

    def __init__(self, **kwargs):
        self.id = 1
        self.persistent_id = 1
        self.name = None
        self.parent = None
        self.is_base = False
        self.is_smart = False
        self.database = None

        self.items = RevisionDict()

        for attr, value in kwargs.iteritems():
            if attr in self.__slots__:
                setattr(self, attr, value)

    def __repr__(self):
        return "<Container(id=%d, name=%s)>" % (self.id, self.name)

    def add_item(self, item):
        """
        """

        # Item should be in the database
        if item.database is None:
            raise ValueError("Item is not associated with a Database")

        self.items[item.id] = item

    def delete_item(self, item):
        """
        """

        del self.items[item.id]

class Item(object):
    __slots__ = ["id", "persistent_id", "type", "file_path", "file_size", "file_suffix", "year",
        "duration", "genre", "artist", "title", "album", "bitrate", "track",
        "is_gapless", "mimetype", "database", "checksum", "artwork"]

    def __init__(self, **kwargs):
        self.id = 1
        self.persistent_id = 1
        self.type = None
        self.file_path = None
        self.file_size = 0
        self.file_suffix = None
        self.year = None
        self.duration = 0
        self.genre = None
        self.artist = None
        self.title = None
        self.album = None
        self.bitrate = 0
        self.track = 0
        self.artwork = None
        self.is_gapless = False
        self.mimetype = None
        self.database = None

        for attr, value in kwargs.iteritems():
            if attr in self.__slots__:
                setattr(self, attr, value)

class Session(object):
    __slots__ = ["revision"]

    def __init__(self):
        self.revision = 1

class Provider(object):

    session_class = Session

    supports_artwork = False

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
            next_revision = self.server.manager.revision

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
        server = self.server.get_revision(revision)

        if delta == 0:
            new = server.databases
            old = None
        else:
            new = server.databases
            old = server.get_revision(delta).databases

        return responses.databases(new, old)

    def get_containers(self, session_id, database_id, revision, delta):
        """
        """

        session = self.sessions[session_id]
        database = self.server.get_revision(revision).databases[database_id]

        if delta == 0:
            new = database.containers
            old = None
        else:
            new = database.containers
            old = database.get_revision(delta).containers

        return responses.containers(new, old)

    def get_container_items(self, session_id, database_id, container_id, revision, delta):
        """
        """

        session = self.sessions[session_id]
        container = self.server.get_revision(revision).databases[database_id].containers[container_id]

        if delta == 0:
            new = container.items
            old = None
        else:
            new = container.items
            old = new = container.get_revision(delta).items

        return responses.container_items(new, old)

    def get_items(self, session_id, database_id, revision, delta):
        """
        """

        session = self.sessions[session_id]
        database = self.server.get_revision(revision).databases[database_id]

        if delta == 0:
            new = database.items
            old = None
        else:
            new = database.items
            old = database.get_revision(delta).items

        return responses.items(new, old)

    def get_item(self, session_id, database_id, item_id, byte_range=None):
        """
        """

        session = self.sessions[session_id]
        database = self.server.get_revision(session.revision).databases[database_id]
        item = database.items[item_id]

        return self.get_item_data(session, item, byte_range)

    def get_artwork(self, session_id, database_id, item_id):
        """
        """

        session = self.sessions[session_id]
        database = self.server.get_revision(session.revision).databases[database_id]
        item = database.items[item_id]

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