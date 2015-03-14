cimport cython

cdef class DAAPObject(object):
    cdef object value
    cdef str code
    cdef int itype

    @cython.locals(level=cython.int)
    cpdef to_tree(self, level=?)

    @cython.locals(length=cython.int, packing=cython.str)
    cpdef encode(self)

    @cython.locals(length=cython.int)
    cpdef decode(self, str stream)


cdef class SpeedyDAAPObject(DAAPObject):
    pass