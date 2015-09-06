from daapserver.collection cimport MutableCollection


cdef class Server(object):
    cdef public long persistent_id
    cdef public object name

    cdef public object databases

    cdef _commit(self, int revision)
    cdef _clean(self, int revision)


cdef class Database(object):
    cdef public int id
    cdef public long persistent_id
    cdef public object name

    cdef public object items
    cdef public object containers

    cdef _commit(self, int revision)
    cdef _clean(self, int revision)


cdef class Item(object):
    cdef public int id
    cdef public long persistent_id
    cdef public int database_id
    cdef public object name
    cdef public object track
    cdef public object artist
    cdef public object album
    cdef public object album_artist
    cdef public object year
    cdef public object bitrate
    cdef public object duration
    cdef public object file_size
    cdef public object file_name
    cdef public object file_type
    cdef public object file_suffix
    cdef public object album_art
    cdef public object genre


cdef class Container(object):
    cdef public int id
    cdef public long persistent_id
    cdef public int database_id
    cdef public object parent_id
    cdef public object name
    cdef public bint is_smart
    cdef public bint is_base

    cdef public object container_items

    cdef _commit(self, int revision)
    cdef _clean(self, int revision)


cdef class ContainerItem(object):
    cdef public int id
    cdef public int database_id
    cdef public int container_id
    cdef public int item_id
    cdef public int order
