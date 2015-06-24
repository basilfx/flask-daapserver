from daapserver.revision cimport RevisionStore

cdef class Collection(object):
    cdef public RevisionStore store
    cdef public int revision