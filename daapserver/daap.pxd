cdef class DAAPObject(object):
    cdef readonly object value
    cdef readonly str code

    cdef int itype


cdef class SpeedyDAAPObject(DAAPObject):
    pass
