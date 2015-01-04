from daapserver cimport constants

cimport cython

cdef class TreeRevisionStorage(object):
    cpdef public int revision
    cdef public int last_operation
    cdef object storage

    @cython.locals(low=cython.int, middle=cython.int, high=cython.int)
    cdef get_index(self, object key, int revision)