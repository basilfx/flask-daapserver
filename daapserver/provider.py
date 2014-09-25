from daapserver import structures, responses, models

import cStringIO

__all__ = ["BaseServer", "BaseDatabase", "BaseContainer", "BaseItem",
           "BaseContainerItem", "Provider", "Session", "LocalFileProvider"]

class BaseObject(object):

    children = []

    def __repr__(self):
        attributes = []

        if hasattr(self, "id"):
            attributes.append("id=%s" % self.id)

        for child, _ in self.children:
            attributes.append("%s=%d" % (child, len(getattr(self, child))))

        return "%s<%s>" % (self.__class__.__name__, ", ".join(attributes))

    def attach(self):
        for child, _ in self.children:
            getattr(self, child).reset()

        for child, propagate in self.children:
            if propagate:
                for item in getattr(self, child).itervalues():
                    item.attach()

    def detach(self):
        for child, _ in self.children:
            getattr(self, child).reset()

        for child, propagate in self.children:
            if propagate:
                for item in getattr(self, child).itervalues():
                    item.detach()

    def get_revision(self, revision):
        class _Proxy(object):
            def __init__(other):
                """
                Construct a new revision proxy.
                """

                for child, propagate in self.children:
                    items = getattr(self, child).get_revision(revision)

                    if propagate:
                        items.wrapper = item.get_revision

                    setattr(other, child, items)
        return _Proxy()

class BaseServer(BaseObject):

    children = [("databases", True)]

    def __init__(self, manager):
        self.manager = manager

        self.databases = structures.RevisionDict(self.manager)

    def add_database(self, *databases):
        for database in databases:
            if not issubclass(type(database), BaseDatabase):
                raise ValueError("Database is not subclass of BaseDatabase")

            if database.manager != self.manager:
                raise ValueError("Database not associated with manager")

        for database in databases:
            database.server = self

            if database.id in self.databases:
                database.items = self.databases[database.id].items
                database.containers = self.databases[database.id].containers

            self.databases[database.id] = database

            database.attach()

    def delete_database(self, *databases):
        for database in databases:
            if not issubclass(type(database), BaseDatabase):
                raise ValueError("Database is not subclass of BaseDatabase")

            if database.manager != self.manager:
                raise ValueError("Database not associated with manager")

        for database in databases:
            database.detach()

            del self.databases[database.id]

            database.server = None

class BaseDatabase(BaseObject):

    children = [("items", False), ("containers", True)]

    def __init__(self, manager):
        self.manager = manager

        self.items = structures.RevisionDict(self.manager)
        self.containers = structures.RevisionDict(self.manager)

    def add_item(self, *items):
        for item in items:
            if not issubclass(type(item), BaseItem):
                raise ValueError("Item is not subclass of BaseItem")

            if item.manager != self.manager:
                raise ValueError("Item not associated with manager")

        for item in items:
            item.database = self

            self.items[item.id] = item

            item.attach()

    def delete_item(self, *items):
        for item in items:
            if not issubclass(type(item), BaseItem):
                raise ValueError("Item is not subclass of BaseItem")

            if item.manager != self.manager:
                raise ValueError("Item not associated with manager")

        for item in items:
            item.detach()

            del self.items[item.id]

            item.database = None

    def add_container(self, *containers):
        for container in containers:
            if not issubclass(type(container), BaseContainer):
                raise ValueError("Container is not subclass of BaseContainer")

            if container.manager != self.manager:
                raise ValueError("Container not associated with manager")

        for container in containers:
            container.database = self

            if container.id in self.containers:
                container.container_items = self.containers[container.id].container_items

            self.containers[container.id] = container

            container.attach()

    def delete_container(self, *containers):
        for container in containers:
            if not issubclass(type(container), BaseContainer):
                raise ValueError("Container is not subclass of BaseContainer")

            if container.manager != self.manager:
                raise ValueError("Container not associated with manager")

        for container in containers:
            container.detach()

            del self.containers[container.id]

            container.database = None

class BaseContainer(BaseObject):

    children = [("container_items", False)]

    def __init__(self, manager):
        self.manager = manager

        self.database = None

        self.container_items = structures.RevisionDict(self.manager)

    def add_container_item(self, *container_items):
        for container_item in container_items:
            if not issubclass(type(container_item), BaseContainerItem):
                raise ValueError("Container item is not subclass of BaseContainerItem")

            if container_item.manager != self.manager:
                raise ValueError("Container item not associated with manager")

        for container_item in container_items:
            self.container_items[container_item.id] = container_item

            container_item.container = self

    def delete_container_item(self, *container_items):
        for container_item in container_items:
            if not issubclass(type(container_item), BaseContainerItem):
                raise ValueError("Container item is not subclass of BaseContainerItem")

            if container_item.manager != self.manager:
                raise ValueError("Container item not associated with manager")

        for container_item in container_items:
            del self.container_items[container_item.id]

            container_item.container = None


class BaseItem(BaseObject):

    def __init__(self, manager):
        self.manager = manager

        self.database = None

class BaseContainerItem(BaseObject):

    def __init__(self, manager):
        self.manager = manager

        self.database = None

        self.container = None
        self.item = None


class Server(BaseServer):
    def __init__(self, manager, **kwargs):
        super(Server, self).__init__(manager)

        self.name = None

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)


class Database(BaseDatabase):
    def __init__(self, manager, **kwargs):
        super(Database, self).__init__(manager)

        self.id = None
        self.persistent_id = None

        self.name = None

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)


class Container(BaseContainer):
    def __init__(self, manager, **kwargs):
        super(Container, self).__init__(manager)

        self.id = None
        self.persistent_id = None

        self.name = None
        self.parent = None
        self.is_smart = False
        self.is_base = False

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)


class Item(BaseItem):
    def __init__(self, manager, **kwargs):
        super(Item, self).__init__(manager)

        self.id = None
        self.persistent_id = None

        self.name = None
        self.track = None
        self.artist = None
        self.album = None
        self.year = None
        self.bitrate = None
        self.duration = None
        self.file_size = None
        self.file_suffix = None
        self.album_art = None

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)


class ContainerItem(BaseContainerItem):
    def __init__(self, manager, **kwargs):
        super(ContainerItem, self).__init__(manager)

        self.id = None
        self.persistent_id = None

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)


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