import cython

cdef class RevisionStore(object):
    """
    """

    def __init__(self):
        self.lookup = dict()
        self.revision = 1
        self.min_revision = 1

    cdef _add(self, object key, Entry value, Entry elder=None):
        """
        """

        if elder is not None:
            value.elder = elder
            value.next = elder.next
            if value.next is not None:
                value.next.previous = value

            value.previous = elder.previous
            if elder.previous is not None:
                value.previous.next = value
            else:
                self.next = value
        else:
            value.previous = None
            value.next = self.next
            self.next = value

            if value.next is not None:
                value.next.previous = value

        # For fast random lookup.
        self.lookup[key] = value

    cdef _check_revision(self, int revision):
        """
        """

        if revision < self.min_revision:
            raise ValueError(
                "Revision %d less than minimal revision %d." % (
                    revision, self.min_revision))

        if revision > self.revision:
            raise ValueError("Revision %d exceeds maximal revision %d." % (
                revision, self.revision))

    def __iter__(self):
        """
        """

        return self.iterate()

    def __nonzero__(self):
        """
        """

        # Return when the first item is yielded. This indicates that the
        # storage is not empty (note that self.next.removed could be True).
        for _ in self.__iter__():
            return True

        return False

    def __contains__(self, key):
        """
        Check whether a given key exists and is not marked as removed.
        """

        cdef Entry current = self.lookup.get(key)

        return current is not None and current.removed != True

    def __repr__(self):
        """
        """

        return "%s(min_revision=%d, revision=%d)" % (
            self.__class__.__name__, self.min_revision, self.revision)

    def iterate(self, int revision=-1):
        """
        """

        cdef Entry current = self.next

        # Optimize for no revision
        if revision == -1:
            while current is not None:
                if not current.removed:
                    yield current.value

                current = current.next
        else:
            self._check_revision(revision)

            while current is not None:
                if revision < current.revision:
                    if current.elder is not None:
                        current = current.elder
                    else:
                        current = current.next
                else:
                    if not current.removed:
                        yield current.value

                    current = current.next

    def commit(self, int revision=-1):
        """
        """

        if revision == -1:
            self.revision += 1
        else:
            if revision < self.revision:
                raise ValueError(
                    "Can only commit to a revision greater than %d (%d was "
                    "given)." % (self.revision, revision))

            self.revision = revision

    def get(self, object key, int revision=-1):
        """
        """

        cdef Entry current = self.lookup[key]

        # Optimize for no revision
        if revision == -1:
            if current.removed:
                raise KeyError("Key '%s' marked as removed." % key)

            return current.value
        else:
            self._check_revision(revision)

            while current is not None:
                if revision < current.revision:
                    current = current.elder
                else:
                    if current.removed:
                        raise KeyError("Key '%s' marked as removed." % key)

                    return current.value

    def remove(self, object key):
        """
        """

        # Wrap in value
        cdef Entry entry = Entry(
            value=None, revision=self.revision, removed=True)

        # Replace in the linked list.
        self._add(key, entry, elder=self.lookup[key])

    def clean(self, int revision=-1):
        """
        """

        cdef Entry current = self.next

        # Optimize for no revision
        if revision == -1:
            while current is not None:
                current.elder = None
                current = current.next
        else:
            self._check_revision(revision)

            while current is not None:
                previous = current

                if revision < current.revision:
                    if current.elder is not None:
                        current = current.elder
                    else:
                        current = current.next
                else:
                    previous.elder = None
                    current = current.next

        # Store minimal revision
        self.min_revision = revision if revision != -1 else self.revision

    def add(self, object key, object value):
        """
        """

        # Wrap in value
        cdef Entry entry = Entry(value=value, revision=self.revision)

        # Add to (or replace in) the linked list
        try:
            self._add(key, entry, elder=self.lookup[key])
        except KeyError:
            self._add(key, entry)

    def diff(self, int revision_a, int revision_b):
        """
        """

        cdef Entry elder
        cdef Entry start
        cdef Entry stop
        cdef int direction
        cdef int status

        self._check_revision(revision_a)
        self._check_revision(revision_b)

        # Swap direction if a < b
        if revision_a < revision_b:
            revision_a, revision_b = revision_b, revision_a
            direction = -1
        else:
            direction = 1

        # Iterate over all keys
        for key in self.lookup:
            elder = self.lookup[key]

            start = None
            stop = None

            # Find the start entry
            while elder is not None:
                if elder.revision <= revision_a:
                    start = elder
                    break

                elder = elder.elder

            if start is None or start.revision < revision_a:
                continue

            # Skip entries of the same revision
            while elder is not None:
                if elder.revision != start.revision:
                    break

                elder = elder.elder

            # Find the stop entry
            while elder is not None:
                if elder.revision <= revision_b:
                    stop = elder
                    break

                elder = elder.elder

            if stop is None:
                yield key, direction
                continue

            # Decide on status
            if revision_a == revision_b:
                if not start.removed:
                    yield key, direction
            else:
                if start.removed and not stop.removed:
                    yield key, -1 * direction
                elif not start.removed and stop.removed:
                    yield key, direction
                elif revision_a == revision_b:
                    yield key, direction
                else:
                    yield key, 0


cdef class Entry(object):
    """
    """

    def __init__(self, object value, int revision, bint removed=False):
        """
        """

        self.value = value
        self.revision = revision
        self.removed = removed

    def __repr__(self):
        """
        """

        return "%s(revision=%d, removed=%s, value=%s)" % (
            self.__class__.__name__, self.revision, self.removed, self.value)
