from libc.stdint cimport uint64_t

cimport cython

cdef class TreeRevisionStorage(object):
    cpdef public int revision
    cdef int last_operation
    cdef object storage

    @cython.locals(low=cython.int, middle=cython.int, high=cython.int)
    cdef get_index(self, uint64_t key, int revision)

    cpdef clear(self, uint64_t parent_key)

    @cython.locals(key=uint64_t)
    cpdef load(self, uint64_t parent_key, object iterable)