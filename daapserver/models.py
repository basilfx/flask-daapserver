from daapserver import revision, utils

import collections


"""
Server
    |
    |
    -   Database
            |
            |
            -   Items
            |
            |
            -   Containers
                    |
                    |
                    -   Container Items

"databases" -> set
"database1.items" -> object
"database1.item1" -> object
"database1.item2" -> object
"database1.containers" -> set
"database1.container1" -> object
"database1.container1.container_items" -> set
"database1.container1.container_item1" -> object
"database1.container1.container_item2" -> object
"database1.container2" -> set
"database1.container2.container_item1" -> object
"database1.container2.container_item2" -> object
"""

class Object(object):
    def __repr__(self):
        attrs = {}

        # Build attribute map
        if hasattr(self, "id"):
            attrs["id"] = self.id

        if hasattr(self, "revision"):
            attrs["revision"] = self.revision

        # Join attributes to single line
        attrs = ", ".join([ "%s=%s" % item for item in attrs.iteritems() ])

        # Done
        return "%s(%s)" % (self.__class__.__name__, attrs)

class Collection(object):

    def __init__(self, parent, clazz, revision=None):
        self.parent = parent
        self.clazz = clazz
        self.revision = revision

    def __call__(self, revision):
        """
        Return a copy of this instance with a different revision number
        """

        # Don't copy if same revision
        if revision == self.revision:
            return self

        return Collection(self.parent, clazz=self.clazz, revision=revision)

    def __getitem__(self, key):
        """
        """

        item = self.parent.storage.get(self.parent.key + (self.clazz, ), key,
            revision=self.revision)

        return item

    def __len__(self):
        try:
            return len(self.parent.storage.get(self.parent.key + (self.clazz, ),
                revision=self.revision))
        except KeyError:
            return 0

    def __iter__(self):
        return self.iterkeys()

    def __repr__(self):
        items = self.parent.storage.get(self.parent.key + (self.clazz, ), revision=self.revision)

        return "%s(%s, revision=%s)" % (self.__class__.__name__, items,
            self.revision)

    def add(self, item):
        if self.revision is not None:
            raise ValueError("Cannot modify old revision.")

        if self.parent.storage is None:
            raise ValueError("Parent has no storage object.")

        # Couple object
        item.storage = self.parent.storage
        item.key = self.parent.key + (self.clazz, item.id)

        self.parent.storage.set(self.parent.key + (self.clazz, ), item.id, item)

    def remove(self, item):
        if self.revision is not None:
            raise ValueError("Cannot modify old revision.")

        if self.parent.storage is None:
            raise ValueError("Parent has no storage object.")

        # Decouple object
        item.storage = None
        item.key = None

        self.parent.storage.delete(self.parent.key + (self.clazz, ), item.id)

    def keys(self):
        return [ key for key in self.iterkeys() ]

    def iterkeys(self):
        try:
            keys = self.parent.storage.get(self.parent.key + (self.clazz, ),
                revision=self.revision, keys=True)
        except KeyError:
            keys = []

        # Yield each key
        for key in keys:
            yield key

    def values(self):
        return [ item for item in self.itervalues() ]

    def itervalues(self):
        try:
            items = self.parent.storage.get(self.parent.key + (self.clazz, ),
                revision=self.revision)
        except KeyError:
            items = []

        # Yield each item
        for item in items:
            yield item

class Server(Object):

    def __init__(self):
        self.storage = revision.TreeRevisionStorage()
        self.key = (Server, )

        self.databases = Collection(self, Database)

        # Properties
        self.name = None

    def to_tree(self):
        return utils.to_tree(self, ("Databases", self.databases))

class Database(Object):
    def __init__(self, storage=None, revision=None):
        self.storage = storage

        self.items = Collection(self, Item, revision=revision)
        self.containers = Collection(self, Container, revision=revision)

        # Properties
        self.persistent_id = None
        self.name = None

    def to_tree(self, indent=0):
        return utils.to_tree(self, ("Items", self.items),
            ("Containers", self.containers))

class Item(Object):
    def __init__(self, storage=None, revision=None):
        self.storage = storage

        # Properties
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

    @property
    def database(self):
        return self.storage.get((Database, self.database_id))

    def to_tree(self):
        return utils.to_tree(self)

class Container(Object):
    def __init__(self, storage=None, revision=None):
        self.storage = storage

        self.container_items = Collection(self, ContainerItem, revision=revision)

        # Properties
        self.persistent_id = None
        self.name = None
        self.parent = None
        self.is_smart = False
        self.is_base = False

    def to_tree(self):
        return utils.to_tree(self, ("Container Items", self.container_items))

class ContainerItem(Object):
    def __init__(self, storage=None, revision=None):
        self.storage = storage

        # Properties
        self.item_id = None
        self.database_id = None
        self.container_id = None

    def to_tree(self):
        return utils.to_tree(self)