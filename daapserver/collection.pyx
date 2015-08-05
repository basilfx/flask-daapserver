cdef class ImmutableCollection(object):

    __slots__ = ()

    # Class type for older versions.
    old_revision_class = ImmutableCollection

    def __init__(self, object parent, RevisionStore store=None,
                  int revision=-1):
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

    def __repr__(self):
        """
        """

        return "%s(revision=%d, store=%s)" % (
            self.__class__.__name__, self.revision, self.store)

    def iterkeys(self):
        for item in self.store.iterate(revision=self.revision):
            yield item.id

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


cdef class MutableCollection(ImmutableCollection):

    __slots__ = ImmutableCollection.__slots__

    def commit(self, int revision):
        self.store.commit(revision)

    def clean(self, int revision):
        self.store.clean(revision)

    def add(self, item):
        self.store.add(item.id, item)

    def remove(self, item):
        self.store.remove(item.id)
