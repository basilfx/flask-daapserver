from daapserver import utils


cdef class Collection(object):

    __slots__ = ()

    def __cinit__(self, object parent, object child_type,
                  RevisionStore store=None, int revision=-1):
        self.parent = parent
        self.child_type = child_type
        self.store = RevisionStore() if store is None else store
        self.revision = revision or -1

    def __call__(self, int revision=-1):
        """
        Return a copy of this instance with a different revision number.
        """

        # Don't copy if same revision
        if revision == self.revision:
            return self

        return self.__class__(
            parent=self.parent, child_type=self.child_type, store=self.store,
            revision=revision)

    def __getitem__(self, key):
        """
        """

        return self.store.get(key, revision=self.revision)

    def __len__(self):
        cdef int count = 0

        for _ in self.store.iterate(revision=self.revision):
            count += 1

        return count

    def __iter__(self):
        return self.iterkeys()

    def add(self, item):
        if self.revision != -1:
            raise ValueError("Cannot modify an old revision.")

        self.store.add(item.id, item)

    def remove(self, item):
        if self.revision != -1:
            raise ValueError("Cannot modify an old revision.")

        self.store.remove(item.id)

    def keys(self):
        return [key for key in self.iterkeys()]

    def iterkeys(self):
        for item in self.store.iterate(revision=self.revision):
            yield item.id

    def values(self):
        return [item for item in self.itervalues()]

    def itervalues(self):
        for item in self.store.iterate(revision=self.revision):
            yield item

    def updated(self, other):
        for key, status in self.store.diff(self.revision, other.revision):
            if status >= 0:
                yield key

    def removed(self, other):
        for key, status in self.store.diff(self.revision, other.revision):
            if status == -1:
                yield key


cdef class Server(object):

    __slots__ = ()

    collection_class = Collection

    def __cinit__(self):
        self.databases = self.collection_class(self, Database)

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

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