from daapserver.revision cimport RevisionStore


cdef class ImmutableCollection(object):
    cdef readonly object parent
    cdef readonly RevisionStore store
    cdef public int revision


cdef class MutableCollection(ImmutableCollection):
    pass


cdef class LazyMutableCollection(MutableCollection):
    cdef public bint busy
    cdef public bint ready
    cdef readonly bint modified
    cdef public pending_commit
    cdef public object iter_item
