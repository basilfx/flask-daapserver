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

        self.databases.commit(revision)

        for database in self.databases.itervalues():
            database._commit(revision)

    cdef _clean(self, int revision):
        """
        """

        cdef Database database

        self.databases.clean(revision)

        for database in self.databases.itervalues():
            database._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, self.databases)


cdef class Database(object):

    __slots__ = ()

    items_collection_class = MutableCollection
    containers_collection_class = MutableCollection

    def __cinit__(self):
        self.items = self.items_collection_class(self)
        self.containers = self.containers_collection_class(self)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        """
        """

        return "%s(id=%d, name=%s)" % (
            self.__class__.__name__, self.id, self.name)

    cdef _commit(self, int revision):
        cdef Container container

        self.items.commit(revision)
        self.containers.commit(revision)

        for container in self.containers.itervalues():
            container._commit(revision)

    cdef _clean(self, int revision):
        cdef Container container

        self.items.clean(revision)
        self.containers.clean(revision)

        for container in self.containers.itervalues():
            container._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, self.items, self.containers)


cdef class Item(object):

    __slots__ = ()

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        """
        """

        return "%s(id=%d, artist=%s, name=%s)" % (
            self.__class__.__name__, self.id, self.artist, self.name)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self)


cdef class Container(object):

    __slots__ = ()

    container_items_collection_class = MutableCollection

    def __cinit__(self):
        self.container_items = self.container_items_collection_class(self)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        """
        """

        return "%s(id=%d, name=%s, is_base=%s)" % (
            self.__class__.__name__, self.id, self.name, self.is_base)

    cdef _commit(self, int revision):
        self.container_items.commit(revision)

    cdef _clean(self, int revision):
        self.container_items.clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self, self.container_items)


cdef class ContainerItem(object):

    __slots__ = ()

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __repr__(self):
        """
        """

        return "%s(id=%d, item_id=%d, order=%d)" % (
            self.__class__.__name__, self.id, self.item_id, self.order)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string
        :rtype str:
        """
        return utils.to_tree(self)
