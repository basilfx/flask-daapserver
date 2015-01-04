from daapserver import revision, constants, utils

KEY_DATABASES = 0x01
KEY_ITEMS = 0x02
KEY_CONTAINERS = 0x03
KEY_CONTAINER_ITEMS = 0x04


class Collection(object):
    __slots__ = ("parent", "key", "revision")

    def __init__(self, parent, key, revision=None):
        self.parent = parent
        self.key = key
        self.revision = revision

    def __call__(self, revision):
        """
        Return a copy of this instance with a different revision number
        """

        # Don't copy if same revision
        if revision == self.revision:
            return self

        return self.__class__(self.parent, self.key, revision=revision)

    def __getitem__(self, key):
        """
        """

        return self.parent.storage.get(
            (self.parent.key << 8) + self.key, key, revision=self.revision)

    def __len__(self):
        try:
            return len(self.parent.storage.get(
                (self.parent.key << 8) + self.key, revision=self.revision))
        except KeyError:
            return 0

    def __iter__(self):
        return self.iterkeys()

    def __repr__(self):
        items = self.parent.storage.get(
            (self.parent.key << 8) + self.key, revision=self.revision)

        return "%s(%s, revision=%s)" % (
            self.__class__.__name__, items, self.revision)

    def add(self, item):
        if self.revision is not None:
            raise ValueError("Cannot modify old revision.")

        if self.parent.storage is None:
            raise ValueError("Parent has no storage object.")

        # Couple object
        item.storage = self.parent.storage
        item.key = (self.parent.key << 32) + (self.key << 24) + item.id

        self.parent.storage.set(
            (self.parent.key << 8) + self.key, item.id, item)

    def remove(self, item):
        if self.revision is not None:
            raise ValueError("Cannot modify old revision.")

        if self.parent.storage is None:
            raise ValueError("Parent has no storage object.")

        # Decouple object
        item.storage = None
        item.key = None

        self.parent.storage.delete((self.parent.key << 8) + self.key, item.id)

    def keys(self):
        return [key for key in self.iterkeys()]

    def iterkeys(self):
        try:
            keys = self.parent.storage.get(
                (self.parent.key << 8) + self.key, revision=self.revision)
        except KeyError:
            keys = []

        # Yield each key
        for key in keys:
            yield key

    def values(self):
        return [item for item in self.itervalues()]

    def itervalues(self):
        try:
            keys = self.parent.storage.get(
                (self.parent.key << 8) + self.key, revision=self.revision)
        except KeyError:
            keys = []

        # Yield each item
        for key in keys:
            yield self[key]

    def edited(self, other):
        key = (self.parent.key << 8) + self.key

        keys = self.parent.storage.get(key, revision=self.revision)
        keys_other = self.parent.storage.get(key, revision=other.revision)

        return {
            k for k in keys & keys_other if self.parent.storage.info(
                key, k, revision=self.revision)[1] == constants.EDIT
        }

    def added(self, other):
        key = (self.parent.key << 8) + self.key

        keys = self.parent.storage.get(key, revision=self.revision)
        keys_other = self.parent.storage.get(key, revision=other.revision)

        return keys - keys_other

    def removed(self, other):
        return other.added(self)


class BaseServer(object):
    __slots__ = ("storage", "key", "id", "databases")

    collection_class = Collection

    def __init__(self):
        self.storage = revision.TreeRevisionStorage()
        self.key = 0

        self.id = None

        self.databases = self.collection_class(self, KEY_DATABASES)

    def to_tree(self):
        return utils.to_tree(self, ("Databases", self.databases))


class BaseDatabase(object):
    __slots__ = (
        "storage", "key", "items", "containers", "id", "persistent_id", "name")

    collection_class = Collection

    def __init__(self, storage=None, revision=None):
        self.storage = storage
        self.key = 0

        self.id = None
        self.persistent_id = None
        self.name = None

        self.items = self.collection_class(self, KEY_ITEMS, revision=revision)
        self.containers = self.collection_class(
            self, KEY_CONTAINERS, revision=revision)

    def to_tree(self, indent=0):
        return utils.to_tree(
            self, ("Items", self.items), ("Containers", self.containers))


class BaseItem(object):
    __slots__ = (
        "storage", "key", "id", "persistent_id", "database_id", "name",
        "track", "artist", "album", "year", "bitrate", "duration", "file_size",
        "file_name", "file_type", "file_suffix", "album_art", "genre")

    def __init__(self, storage=None, revision=None):
        self.storage = storage
        self.key = 0

        self.id = None
        self.persistent_id = None
        self.database_id = None
        self.name = None
        self.track = None
        self.artist = None
        self.album = None
        self.year = None
        self.bitrate = None
        self.duration = None
        self.file_size = None
        self.file_name = None
        self.file_type = None
        self.file_suffix = None
        self.album_art = None
        self.genre = None

    def to_tree(self):
        return utils.to_tree(self)


class BaseContainer(object):
    __slots__ = (
        "storage", "key", "container_items", "id", "database_id",
        "persistent_id", "parent_id", "name", "is_smart", "is_base")

    collection_class = Collection

    def __init__(self, storage=None, revision=None):
        self.storage = storage
        self.key = 0

        self.id = None
        self.persistent_id = None
        self.database_id = None
        self.parent_id = None
        self.name = None
        self.is_smart = None
        self.is_base = None

        self.container_items = self.collection_class(
            self, KEY_CONTAINER_ITEMS, revision=revision)

    def to_tree(self):
        return utils.to_tree(self, ("Container Items", self.container_items))


class BaseContainerItem(object):
    __slots__ = (
        "storage", "key", "id", "persistent_id", "container_id", "database_id",
        "item_id", "order")

    def __init__(self, storage=None, revision=None):
        self.storage = storage
        self.key = 0

        self.id = None
        self.persistent_id = None
        self.container_id = None
        self.database_id = None
        self.item_id = None
        self.order = None

    def to_tree(self):
        return utils.to_tree(self)


class Server(BaseServer):
    """
    Wrapper for BaseServer with kwargs support.
    """

    __slots__ = BaseServer.__slots__

    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Database(BaseDatabase):
    """
    Wrapper for BaseDatabase with kwargs support.
    """

    __slots__ = BaseDatabase.__slots__

    def __init__(self, *args, **kwargs):
        super(Database, self).__init__(*args)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Container(BaseContainer):
    """
    Wrapper for BaseContainer with kwargs support.
    """

    __slots__ = BaseContainer.__slots__

    def __init__(self, *args, **kwargs):
        super(Container, self).__init__(*args)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class Item(BaseItem):
    """
    Wrapper for BaseItem with kwargs support.
    """

    __slots__ = BaseItem.__slots__

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)


class ContainerItem(BaseContainerItem):
    """
    Wrapper for BaseContainerItem with kwargs support.
    """

    __slots__ = BaseContainerItem.__slots__

    def __init__(self, *args, **kwargs):
        super(ContainerItem, self).__init__(*args)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)
