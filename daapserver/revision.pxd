cdef class RevisionStore(object):
    cdef Entry next
    cdef readonly dict lookup
    cdef readonly int revision
    cdef readonly int min_revision

    cdef _add(self, object key, Entry value, Entry elder=?)

    cdef _check_revision(self, int revision)


cdef class Entry(object):
    cdef object value
    cdef int revision
    cdef bint removed

    cdef Entry previous, next, elder
