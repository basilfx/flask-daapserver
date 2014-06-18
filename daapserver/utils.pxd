cimport cython

@cython.locals(begin=cython.long, end=cython.long)
cpdef tuple parse_byte_range(tuple byte_range, unsigned long min_byte=?, unsigned long max_byte=?)

cdef class Mapping(object):
    pass