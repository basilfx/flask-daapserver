from daapserver import utils

import copy


cdef class Server(object):

    __slots__ = ()

    databases_collection_class = MutableCollection

    def __init__(self, **kwargs):
        """
        Initialize a new Server. Copies any key-value from kwargs to the
        attributes of this instance.

        The Server is the only instance that does not require an ID.
        """

        self.databases = self.databases_collection_class(self)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __copy__(self):
        """
        Return a copy of this instance.

        :return: Copy of this instance.
        :rtype Server:
        """

        cdef Server result = <Server> copy.copy(super(Server, self))

        result.persistent_id = self.persistent_id
        result.name = self.name

        result.databases = self.databases

        return result

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(name=%s)" % (self.__class__.__name__, self.name)

    def __str__(self):
        """
        Return a string representation of this instance. Any non-ASCII
        characters will be replaced.

        :return: String representation.
        :rtype str:
        """

        return unicode(self).encode("ascii", "replace")

    def __repr__(self):
        """
        Return instance representation. Uses the `__str__' method.

        :return: String representation.
        :rtype str:
        """

        return str(self)

    def commit(self, int revision):
        """
        Propagate a commit to all models that are part of this instance and
        their children.

        :param int revision: Revision to commit to.
        """

        self._commit(revision)

    def clean(self, int revision):
        """
        Propagate a clean to all models that are part of this instance and
        their children.

        :param int revision: Revision to clean up to.
        """

        self._clean(revision)

    cdef _commit(self, int revision):
        """
        Actual implementation of the commit method. Propagates the commit to
        items in the collections.
        """

        cdef Database database

        self.databases.commit(revision)

        for database in self.databases.itervalues():
            database._commit(revision)

    cdef _clean(self, int revision):
        """
        Actual implementation of the clean method. Propagates the clean to
        items in the collections.
        """

        cdef Database database

        self.databases.clean(revision)

        for database in self.databases.itervalues():
            database._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string.
        :rtype str:
        """
        return utils.to_tree(self, self.databases)


cdef class Database(object):

    __slots__ = ()

    items_collection_class = MutableCollection
    containers_collection_class = MutableCollection

    def __init__(self, **kwargs):
        """
        Initialize a new Database. Copies any key-value from kwargs to the
        attributes of this instance.
        """

        self.items = self.items_collection_class(self)
        self.containers = self.containers_collection_class(self)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __copy__(self):
        """
        Return a copy of this instance.

        :return: Copy of this instance.
        :rtype Database:
        """

        cdef Database result = <Database> copy.copy(super(Database, self))

        result.id = self.id
        result.persistent_id = self.persistent_id
        result.name = self.name

        result.items = self.items
        result.containers = self.containers

        return result

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(id=%d, name=%s)" % (
            self.__class__.__name__, self.id, self.name)

    def __str__(self):
        """
        Return a string representation of this instance. Any non-ASCII
        characters will be replaced.

        :return: String representation.
        :rtype str:
        """

        return unicode(self).encode("ascii", "replace")

    def __repr__(self):
        """
        Return instance representation. Uses the `__str__' method.

        :return: String representation.
        :rtype str:
        """

        return str(self)

    cdef _commit(self, int revision):
        """
        Actual implementation of the commit method. Propagates the commit to
        items in the collections.
        """

        cdef Container container

        self.items.commit(revision)
        self.containers.commit(revision)

        for container in self.containers.itervalues():
            container._commit(revision)

    cdef _clean(self, int revision):
        """
        Actual implementation of the clean method. Propagates the clean to
        items in the collections.
        """

        cdef Container container

        self.items.clean(revision)
        self.containers.clean(revision)

        for container in self.containers.itervalues():
            container._clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string.
        :rtype str:
        """
        return utils.to_tree(self, self.items, self.containers)


cdef class Item(object):

    __slots__ = ()

    def __init__(self, **kwargs):
        """
        Initialize a new Item. Copies any key-value from kwargs to the
        attributes of this instance.
        """

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __copy__(self):
        """
        Return a copy of this instance.

        :return: Copy of this instance.
        :rtype Item:
        """

        cdef Item result = <Item> copy.copy(super(Item, self))

        result.id = self.id
        result.persistent_id = self.persistent_id
        result.database_id = self.database_id
        result.name = self.name
        result.track = self.track
        result.artist = self.artist
        result.album = self.album
        result.album_artist = self.album_artist
        result.year = self.year
        result.bitrate = self.bitrate
        result.duration = self.duration
        result.file_size = self.file_size
        result.file_name = self.file_name
        result.file_type = self.file_type
        result.file_suffix = self.file_suffix
        result.album_art = self.album_art
        result.genre = self.genre

        return result

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(id=%d, artist=%s, name=%s)" % (
            self.__class__.__name__, self.id, self.artist, self.name)

    def __str__(self):
        """
        Return a string representation of this instance. Any non-ASCII
        characters will be replaced.

        :return: String representation.
        :rtype str:
        """

        return unicode(self).encode("ascii", "replace")

    def __repr__(self):
        """
        Return instance representation. Uses the `__str__' method.

        :return: String representation.
        :rtype str:
        """

        return str(self)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string.
        :rtype str:
        """
        return utils.to_tree(self)


cdef class Container(object):

    __slots__ = ()

    container_items_collection_class = MutableCollection

    def __init__(self, **kwargs):
        """
        Initialize a new Container. Copies any key-value from kwargs to the
        attributes of this instance.
        """

        self.container_items = self.container_items_collection_class(self)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __copy__(self):
        """
        Return a copy of this instance.

        :return: Copy of this instance.
        :rtype Container:
        """

        cdef Container result = <Container> copy.copy(super(Container, self))

        result.id = self.id
        result.persistent_id = self.persistent_id
        result.database_id = self.database_id
        result.parent_id = self.parent_id
        result.name = self.name
        result.is_smart = self.is_smart
        result.is_base = self.is_base

        result.container_items = self.container_items

        return result

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(id=%d, name=%s, is_base=%s)" % (
            self.__class__.__name__, self.id, self.name, self.is_base)

    def __str__(self):
        """
        Return a string representation of this instance. Any non-ASCII
        characters will be replaced.

        :return: String representation.
        :rtype str:
        """

        return unicode(self).encode("ascii", "replace")

    def __repr__(self):
        """
        Return instance representation. Uses the `__str__' method.

        :return: String representation.
        :rtype str:
        """

        return str(self)

    cdef _commit(self, int revision):
        """
        Actual implementation of the commit method. Propagates the commit to
        items in the collections.
        """

        self.container_items.commit(revision)

    cdef _clean(self, int revision):
        """
        Actual implementation of the clean method. Propagates the clean to
        items in the collections.
        """

        self.container_items.clean(revision)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string.
        :rtype str:
        """
        return utils.to_tree(self, self.container_items)


cdef class ContainerItem(object):

    __slots__ = ()

    def __init__(self, **kwargs):
        """
        Initialize a new ContainerItem. Copies any key-value from kwargs to the
        attributes of this instance.
        """

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def __copy__(self):
        """
        Return a copy of this instance.

        :return: Copy of this instance.
        :rtype ContainerItem:
        """

        cdef ContainerItem result = <ContainerItem> copy.copy(
            super(ContainerItem, self))

        result.id = self.id
        result.database_id = self.database_id
        result.container_id = self.container_id
        result.item_id = self.item_id
        result.order = self.order

        return result

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(id=%d, item_id=%d, order=%d)" % (
            self.__class__.__name__, self.id, self.item_id, self.order)

    def __str__(self):
        """
        Return a string representation of this instance. Any non-ASCII
        characters will be replaced.

        :return: String representation.
        :rtype str:
        """

        return unicode(self).encode("ascii", "replace")

    def __repr__(self):
        """
        Return instance representation. Uses the `__str__' method.

        :return: String representation.
        :rtype str:
        """

        return str(self)

    def to_tree(self):
        """
        Generate a tree representation of this object and children.

        :return: Tree representation as a string.
        :rtype str:
        """
        return utils.to_tree(self)
