cdef class DAAPObject(object):
    cdef object value
    cdef str code
    cdef int itype


cdef class SpeedyDAAPObject(DAAPObject):
    pass
