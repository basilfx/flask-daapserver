cdef class Collection(object):

    def __cinit__(self, RevisionStore store=None, int revision=-1):
        self.store = RevisionStore() if store is None else store
        self.revision = revision or -1

    def __call__(self, int revision=-1):
        """
        Return a copy of this instance with a different revision number.
        """

        # Don't copy if same revision
        if revision == self.revision:
            return self

        return self.__class__(store=self.store, revision=revision)

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
