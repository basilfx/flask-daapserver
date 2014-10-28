cimport cython

cdef class TreeRevisionStorage(object):
    cpdef public int revision
    cdef int last_operation
    cdef object storage

    @cython.locals(low=cython.int, middle=cython.int, high=cython.int)
    cdef get_index(self, long key, int revision)

    cpdef clear(self, long parent_key)

    @cython.locals(key=cython.long)
    cpdef load(self, long parent_key, object iterable)