from daapserver.revision cimport RevisionStore


cdef class ImmutableCollection(object):
    cdef readonly object parent
    cdef readonly RevisionStore store
    cdef public int revision


cdef class MutableCollection(ImmutableCollection):
    pass
