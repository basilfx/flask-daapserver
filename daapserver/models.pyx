from daapserver import utils


cdef class Server(object):

    __slots__ = ()

    databases_collection_class = MutableCollection

    def __cinit__(self):
        self.databases = self.databases_collection_class(self)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        """
        """

        return "%s(name=%s, revision=%d)" % (
            self.__class__.__name__, self.name, self.revision)

    def commit(self):
        """
        """

        self.revision += 1

        self._commit(self.revision + 1)

    def clean(self, int revision):
        """
        """

        self._clean(revision)

    cdef _commit(self, int revision):
        """
        """

        cdef Database database

        self.databases.store.commit(revision)

        for database in self.databases.itervalues():
            database._commit(revision)

    cdef _clean(self, int revision):
        """
        """

        cdef Database database

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

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.items = self.collection_class(self, Item)
        self.containers = self.collection_class(self, Container)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    cdef _commit(self, int revision):
        cdef Container container

        self.items.store.commit(revision)
        self.containers.store.commit(revision)

        for container in self.containers.itervalues():
            container._commit(revision)

    cdef _clean(self, int revision):
        cdef Container container

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

    __slots__ = ()

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

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.container_items = self.collection_class(self, ContainerItem)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    cdef _commit(self, int revision):
        self.container_items.store.commit(revision)

    cdef _clean(self, int revision):
        self.container_items.store.clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, ("Container Items", self.container_items))


cdef class ContainerItem(object):

    __slots__ = ()

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