cimport cython

cdef class DAAPObject(object):
    cdef object value
    cdef object code
    cdef int itype

    @cython.locals(level=cython.int)
    cpdef to_tree(self, level=?)

    @cython.locals(length=cython.int)
    cpdef encode(self)

    @cython.locals(length=cython.int)
    cpdef decode(self, str stream)