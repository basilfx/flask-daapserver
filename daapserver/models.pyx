from daapserver.collection import Collection
from daapserver import utils


cdef class Server(object):
    cdef public int revision

    cdef public object name

    cdef public object databases

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.revision = 0

        self.name = None

        self.databases = self.collection_class()

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def commit(self):
        """
        """

        self.revision += 1

        self._commit(self.revision + 1)

    def clean(self, revision):
        """
        """

        self._clean(revision)

    def _commit(self, revision):
        """
        """

        self.databases.store.commit(revision)

        for database in self.databases.itervalues():
            database._commit(revision)

    def _clean(self, revision):
        """
        """

        self.databases.store.clean(revision)

        for database in self.databases.itervalues():
            database._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, ("Databases", self.databases))


cdef class Database(object):
    cdef public int id
    cdef public int persistent_id
    cdef public object name

    cdef public object items
    cdef public object containers

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.id = 0
        self.persistent_id = 0
        self.name = None

        self.items = self.collection_class()
        self.containers = self.collection_class()

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def _commit(self, revision):
        self.items.store.commit(revision)
        self.containers.store.commit(revision)

        for container in self.containers.itervalues():
            container._commit(revision)

    def _clean(self, revision):
        self.items.store.clean(revision)
        self.containers.store.clean(revision)

        for container in self.containers.itervalues():
            container._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(
            self, ("Items", self.items), ("Containers", self.containers))


cdef class Item(object):
    cdef public int id
    cdef public int persistent_id
    cdef public int database_id
    cdef public object name
    cdef public object track
    cdef public object artist
    cdef public object album
    cdef public object year
    cdef public object bitrate
    cdef public object duration
    cdef public object file_size
    cdef public object file_name
    cdef public object file_type
    cdef public object file_suffix
    cdef public object album_art
    cdef public object genre

    __slots__ = ()

    def __cinit__(self):
        self.id = 0
        self.persistent_id = 0
        self.database_id = 0
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

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self)


cdef class Container(object):
    cdef public int id
    cdef public int persistent_id
    cdef public int database_id
    cdef public int parent_id
    cdef public object name
    cdef public bint is_smart
    cdef public bint is_base

    cdef public object container_items

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.id = 0
        self.persistent_id = 0
        self.database_id = 0
        self.parent_id = 0
        self.name = None
        self.is_smart = False
        self.is_base = False

        self.container_items = self.collection_class()

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def _commit(self, revision):
        self.container_items.store.commit(revision)

    def _clean(self, revision):
        self.container_items.store.clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, ("Container Items", self.container_items))


cdef class ContainerItem(object):
    cdef public int id
    cdef public int database_id
    cdef public int container_id
    cdef public int item_id
    cdef public int order

    __slots__ = ()

    def __cinit__(self):
        self.id = 0
        self.database_id = 0
        self.container_id = 0
        self.item_id = 0
        self.order = 0

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self)