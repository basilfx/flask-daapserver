cdef class ImmutableCollection(object):

    __slots__ = ()

    # Class type for older versions.
    old_revision_class = ImmutableCollection

    def __init__(self, object parent, RevisionStore store=None,
                  int revision=-1):
        """
        """

        self.parent = parent
        self.store = RevisionStore() if store is None else store
        self.revision = revision or -1

    def __call__(self, int revision=-1):
        """
        Return a copy of this instance with a different revision number.
        """

        # Don't copy if same revision
        if revision == self.revision:
            return self

        # Return new instance, which is of type `self.old_collection_class`.
        return self.old_revision_class(
            parent=self.parent, store=self.store, revision=revision)

    def __contains__(self, key):
        """
        """

        try:
            return self.store.get(key, revision=self.revision)
        except KeyError:
            return False

    def __getitem__(self, key):
        """
        """

        return self.store.get(key, revision=self.revision)

    def __len__(self):
        """
        """

        cdef int count = 0

        for _ in self.store.iterate(revision=self.revision):
            count += 1

        return count

    def __iter__(self):
        """
        """

        return self.iterkeys()

    def __unicode__(self):
        """
        Return an unicode representation of this instance.

        :return: Unicode representation.
        :rtype unicode:
        """

        return u"%s(revision=%d, store=%s)" % (
            self.__class__.__name__, self.revision, self.store)

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

    def iterkeys(self):
        """
        """

        for item in self.store.iterate(revision=self.revision):
            yield item.id

    def itervalues(self):
        """
        """

        for item in self.store.iterate(revision=self.revision):
            yield item

    def keys(self):
        """
        """

        return list(self.iterkeys())

    def values(self):
        """
        """

        return list(self.itervalues())

    def updated(self, other):
        """
        """

        for key, status in self.store.diff(self.revision, other.revision):
            if status >= 0:
                yield key

    def removed(self, other):
        """
        """

        for key, status in self.store.diff(self.revision, other.revision):
            if status == -1:
                yield key


cdef class MutableCollection(ImmutableCollection):

    __slots__ = ImmutableCollection.__slots__

    def commit(self, int revision):
        """
        """

        self.store.commit(revision)

    def clean(self, int revision):
        """
        """

        self.store.clean(revision)

    def add(self, item):
        """
        """

        self.store.add(item.id, item)

    def remove(self, item):
        """
        """

        self.store.remove(item.id)


cdef class LazyMutableCollection(MutableCollection):
    """
    A lazy mutable collection is similar to a mutable collection, except that
    it does not load all items at once, but items are only loaded when
    requested for. This means that there is another backend providing the
    items, such as a database.

    A class that extends this class should implement a `load([item_ids)'
    method that yield all items, or (re-)loads `item_ids'. Furthermore, a
    `count()' method is required to provide a count method that efficiently
    returns the number of objects in this collection.
    """

    __slots__ = MutableCollection.__slots__

    def __init__(self, *args, **kwargs):
        """
        """

        super(LazyMutableCollection, self).__init__(*args, **kwargs)

        self.busy = False
        self.ready = False
        self.modified = False
        self.pending_commit = -1
        self.iter_item = None

    def count(self):
        """
        Return the number of items in this collection, without loading the
        items in memory. For instance, a DB could execute a COUNT query to
        yield te result

        :return: Number of items in this collection
        :rtype int:
        """

        raise NotImplementedError("Needs to be overridden.")

    def load(self, item_ids=None):
        """
        Load items into memory. If `item_ids' is None, then load all items into
        memory, otherwise limit to that IDs.
        """

        raise NotImplementedError("Needs to be overridden.")

    def update_ids(self, item_ids):
        """
        """

        # Don't update if this instance isn't ready.
        if not self.ready:
            return

        for _ in self.load(item_ids):
            pass

    def remove_ids(self, item_ids):
        """
        """

        # Don't remove items if this instance isn't ready.
        if not self.ready:
            return

        for item_id in item_ids:
            self.store.remove(item_id)

    def commit(self, int revision):
        """
        """

        # Store commit if not yet ready. It will be commited when items are
        # loaded.
        if self.modified and not self.ready:
            self.pending_commit = revision
        else:
            super(LazyMutableCollection, self).commit(revision)

    def clean(self, int revision):
        """
        """

        if self.modified and self.pending_commit != -1:
            raise ValueError("A pending commit is left.")

        super(LazyMutableCollection, self).clean(revision)

    def add(self, item):
        """
        """

        self.modified = True
        super(LazyMutableCollection, self).add(item)

    def remove(self, item):
        """
        """

        self.modified = True
        super(LazyMutableCollection, self).remove(item)

    def __contains__(self, key):
        """
        """

        if not self.ready:
            for _ in self.load():
                pass

        return super(LazyMutableCollection, self).__contains__(key)

    def __len__(self):
        """
        """

        if not self.ready:
            return self.count()

        return super(LazyMutableCollection, self).__len__()

    def __contains__(self, key):
        """
        """

        if not self.ready:
            for _ in self.load():
                pass

        return super(LazyMutableCollection, self).__contains__(key)

    def __getitem__(self, key):
        """
        """

        if self.busy and self.iter_item.id == key:
            return self.iter_item

        if not self.ready:
            try:
                return super(LazyMutableCollection, self).__getitem__(key)
            except KeyError:
                for _ in self.load():
                    pass

        return super(LazyMutableCollection, self).__getitem__(key)

    def iterkeys(self):
        """
        """

        if not self.ready:
            for item in self.load():
                yield item.id
        else:
            for key in super(LazyMutableCollection, self).iterkeys():
                yield key

    def itervalues(self):
        """
        """

        if not self.ready:
            for item in self.load():
                yield item
        else:
            for item in super(LazyMutableCollection, self).itervalues():
                yield item
