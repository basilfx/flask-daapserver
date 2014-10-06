from daapserver import revision, utils

import collections

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

        return Collection(self.parent, self.key, revision=revision)

    def __getitem__(self, key):
        """
        """

        return self.parent.storage.get((self.parent.key << 8) + self.key,
            key, revision=self.revision)

    def __len__(self):
        try:
            return len(self.parent.storage.get((self.parent.key << 8) + \
                self.key, revision=self.revision))
        except KeyError:
            return 0

    def __iter__(self):
        return self.iterkeys()

    def __repr__(self):
        items = self.parent.storage.get((self.parent.key << 8) + self.key,
            revision=self.revision)

        return "%s(%s, revision=%s)" % (self.__class__.__name__, items,
            self.revision)

    def add(self, item):
        if self.revision is not None:
            raise ValueError("Cannot modify old revision.")

        if self.parent.storage is None:
            raise ValueError("Parent has no storage object.")

        # Couple object
        item.storage = self.parent.storage
        item.key = (self.parent.key << 32) + (self.key << 24) + item.id

        self.parent.storage.set((self.parent.key << 8) + self.key, item.id,
            item)

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
        return [ key for key in self.iterkeys() ]

    def iterkeys(self):
        try:
            keys = self.parent.storage.get((self.parent.key << 8) + self.key,
                revision=self.revision)
        except KeyError:
            keys = []

        # Yield each key
        for key in keys:
            yield key

    def values(self):
        return [ item for item in self.itervalues() ]

    def itervalues(self):
        try:
            items = self.parent.storage.get((self.parent.key << 8) + self.key,
                revision=self.revision)
        except KeyError:
            items = []

        # Yield each item
        for item in items:
            yield self[item]

    def edited(self, other):
        key = (self.parent.key << 8) + self.key

        keys = self.parent.storage.get(key, revision=self.revision)
        keys_other = self.parent.storage.get(key, revision=other.revision)

        return { k for k in keys & keys_other if self.parent.storage.info(
            key, k, revision=self.revision)[1] == revision.EDIT }

    def added(self, other):
        key = (self.parent.key << 8) + self.key

        keys = self.parent.storage.get(key, revision=self.revision)
        keys_other = self.parent.storage.get(key, revision=other.revision)

        return keys - keys_other

    def removed(self, other):
        return other.added(self)

class Server(object):
    __slots__ = ("storage", "key", "id", "databases")

    def __init__(self, **kwargs):
        self.storage = revision.TreeRevisionStorage()
        self.key = 0
        self.id = 0

        self.databases = Collection(self, 0x01)

        # Set properties
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def to_tree(self):
        return utils.to_tree(self, ("Databases", self.databases))

class Database(object):
    __slots__ = ("storage", "key", "items", "containers", "id", "persistent_id",
        "name")

    def __init__(self, storage=None, revision=None, **kwargs):
        self.storage = storage

        self.items = Collection(self, 0x02, revision=revision)
        self.containers = Collection(self, 0x03, revision=revision)

        # Properties
        self.persistent_id = None
        self.name = None

        # Set properties
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def to_tree(self, indent=0):
        return utils.to_tree(self, ("Items", self.items),
            ("Containers", self.containers))

class Item(object):
    __slots__ = ("storage", "key", "id", "persistent_id", "name", "track",
        "artist", "album", "year", "bitrate", "duration", "file_size",
        "file_name", "file_type", "file_suffix", "album_art", "genre")

    def __init__(self, storage=None, revision=None, **kwargs):
        self.storage = storage
        self.key = None

        # Properties
        self.id = None
        self.persistent_id = None
        self.name = None
        self.track = None
        self.artist = None
        self.album = None
        self.year = None
        self.genre = None
        self.bitrate = None
        self.duration = None
        self.file_name = None
        self.file_type = None
        self.file_size = None
        self.file_suffix = None
        self.album_art = None

        # Set properties
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def to_tree(self):
        return utils.to_tree(self)

class Container(object):
    __slots__ = ("storage", "key", "container_items", "id", "persistent_id",
        "name", "parent", "is_smart", "is_base")

    def __init__(self, storage=None, revision=None, **kwargs):
        self.storage = storage
        self.key = None

        self.container_items = Collection(self, 0x04, revision=revision)

        # Properties
        self.id = None
        self.persistent_id = None
        self.name = None
        self.parent = None
        self.is_smart = False
        self.is_base = False

        # Set properties
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def to_tree(self):
        return utils.to_tree(self, ("Container Items", self.container_items))

class ContainerItem(object):
    __slots__ = ("storage", "key", "id", "persistent_id", "item", "order")

    def __init__(self, storage=None, revision=None, **kwargs):
        self.storage = storage
        self.key = None

        # Properties
        self.id = None
        self.persistent_id = None
        self.item = None
        self.order = None

        # Set properties
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)

    def to_tree(self):
        return utils.to_tree(self)