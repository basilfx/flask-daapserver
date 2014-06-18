cimport cython

from utils cimport Mapping

cdef class RevisionManager(object):
    cdef public int revision

    cdef tuple last_operation
    cdef int last_revision
    cdef dict sources

    cpdef bint is_conflicting(self, int operation, object source, object item)

cdef class RevisionDictView(Mapping):
    cdef public int revision
    cdef public object wrapper
    cdef public object backend

    cdef dict changes
    cdef set all_keys

cdef class RevisionDict(Mapping):
    cpdef public object backend
    cpdef RevisionManager manager

    cdef int local_revision
    cdef dict last_log
    cdef set last_log_keys
    cdef object log
    cdef object log_keys
    cdef list revisions

    @cython.locals(revision=cython.int)
    cpdef int find_revision(self, int target_revision)

    @cython.locals(aligned=cython.int)
    cpdef get_revision(self, int revision)