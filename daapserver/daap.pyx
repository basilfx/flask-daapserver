# daap.py
#
# DAAP classes and methods.
#
# original work (c) 2004, Davyd Madeley <davyd@ucc.asn.au>
#
# Later iTunes authentication work and object model
# copyright 2005 Tom Insam <tom@jerakeen.org>
#
# Stripped clean + a few bug fixes, Erik Hetzner
#
# Stripped more clean + more bug fixes, Bas Stottelaar

from daapserver.daap_data import dmap_data_types, dmap_names, \
    dmap_reverse_data_types, dmap_code_types

import struct


cdef class DAAPObject(object):
    """
    Represent a DAAP data object.
    """

    def __init__(self, str name=None, object value=None):
        """
        Create a new DAAPObject. The name must be an existing property in the
        `daapserver.daap_data' module.

        If `name' is None, an empty object is instantiated.

        :param str name: Name of DAAP property (optional).
        :param object value: Value of DAAP property (optional).
        """

        if name is not None:
            try:
                self.code = dmap_names[name]
            except KeyError:
                raise ValueError("Unexpected code '%s'" % name)

            self.itype = dmap_code_types[self.code][1]
            self.value = value

    def to_tree(self, int level=0):
        """
        Convert a DAAPObject to a tree representation.

        :param int level: Current level.
        """

        yield "\t" * level + "%s (%s)\t%s\t%s\n" % (
            dmap_code_types[self.code][0], self.code,
            dmap_reverse_data_types[self.itype], self.value)

        if self.itype == 12:
            for obj in self.value:
                yield obj.to_tree(level + 1)

    def encode(self):
        """
        Encode a DAAPObject instance.

        :return: Serialized string representation of object.
        :rtype: str
        """

        cdef int length
        cdef str packing
        cdef bytearray data
        cdef object value

        # Generate DMAP tagged data format. Find out what type of object
        # this is.
        if self.itype == 12:
            # Object is a container. This means the items within `self.value'.
            # are inspected.
            data = bytearray()
            for item in self.value:
                data.extend(item.encode())

            # Get the length of the data
            length = len(data)

            # Pack data: 4 byte code, 4 byte length, length bytes of data.
            try:
                return struct.pack(
                    "!4sI%ds" % length, self.code, length, str(data))
            except struct.error as e:
                raise ValueError(
                    "Error while packing code '%s' ('%s'): %s" %
                    (self.code, dmap_code_types[self.code][0], e))
        else:
            value = self.value

            # Determine the packing
            if self.itype == 11:
                parts = value.split(".")
                value = struct.pack("!HH", int(parts[0]), int(parts[2]))
                packing = "4s"
                length = 4
            elif self.itype == 7:
                packing = "q"
                length = 8
            elif self.itype == 8:
                packing = "Q"
                length = 8
            elif self.itype == 5:
                if type(value) == str and len(value) <= 4:
                    packing = "4s"
                    length = 4
                else:
                    packing = "i"
                    length = 4
            elif self.itype == 6:
                packing = "I"
                length = 4
            elif self.itype == 3:
                packing = "h"
                length = 2
            elif self.itype == 4:
                packing = "H"
                length = 2
            elif self.itype == 1:
                packing = "b"
                length = 1
            elif self.itype == 2:
                packing = "B"
                length = 1
            elif self.itype == 10:
                packing = "I"
                length = 4
            elif self.itype == 9:
                if type(value) == unicode:
                    value = value.encode("utf-8")

                length = len(value)
                packing = "%ss" % length
            else:
                raise ValueError(
                    "Unexpected type %d" % dmap_reverse_data_types[self.itype])

            # Pack data: 4 characters for the code, 4 bytes for the length
            # and length bytes for the value
            try:
                return struct.pack(
                    "!4sI%s" % packing, self.code, length, value)
            except struct.error as e:
                raise ValueError(
                    "Error while packing code '%s' ('%s'): %s" % (
                        self.code, dmap_code_types[self.code][0], e))

    def decode(self, stream):
        """
        Decode a stream to DAAPObjects.

        :param stream Stream: Data stream (e.g. cStringIO).
        """

        cdef int length
        cdef int start_pos
        cdef str data

        # Read 4 bytes for the code and 4 bytes for the length of the
        # objects data.
        data = stream.read(8)

        try:
            self.code, length = struct.unpack("!4sI", data)
        except struct.error as e:
            raise ValueError("Error while unpacking code: %s" % e)

        # Now we need to find out what type of object it is
        try:
            self.itype = dmap_code_types[self.code][1]
        except KeyError:
            raise ValueError("Unknown code '%s'" % self.code)

        if self.itype == 12:
            start_pos = stream.tell()
            self.value = []

            # The object is a container, we need to pass it its length
            # amount of data for processessing
            while stream.tell() < start_pos + length:
                obj = DAAPObject()
                self.value.append(obj)
                obj.decode(stream)
        else:
            # Not a container, we're a single atom. Read it.
            data = stream.read(length)

            if self.itype == 7:
                value = struct.unpack("!q", data)[0]
            elif self.itype == 8:
                value = struct.unpack("!Q", data)[0]
            elif self.itype == 5:
                value = struct.unpack("!i", data)[0]
            elif self.itype == 6:
                value = struct.unpack("!I", data)[0]
            elif self.itype == 3:
                value = struct.unpack("!h", data)[0]
            elif self.itype == 4:
                value = struct.unpack("!H", data)[0]
            elif self.itype == 1:
                value = struct.unpack("!b", data)[0]
            elif self.itype == 2:
                value = struct.unpack("!B", data)[0]
            elif self.itype == 11:
                value = float("%s.%s" % struct.unpack("!HH", data))
            elif self.itype == 10:
                value = struct.unpack("!I", data)[0]
            elif self.itype == 9:
                # The object is a string. The string's length is important.
                try:
                    value = unicode(struct.unpack(
                        "!%ss" % length, data)[0], "utf-8")
                except UnicodeDecodeError:
                    value = unicode(struct.unpack(
                        "!%ss" % length, data)[0], "latin-1")
            else:
                raise ValueError(
                    "Unexpected type '%s'" % dmap_data_types[self.itype])

            self.value = value


cdef class SpeedyDAAPObject(DAAPObject):
    """
    Extension of DAAPObject that directly sets the values. This does not check
    the values.
    """

    def __init__(self, str code, int itype, object value):
        """
        Instantiate a new SpeedyDAAPObject. This constructor bypasses checks.

        :param str code: DAAP property code.
        :param int itype: Code representing value type (see
                          `daapserver.daap_data)'.
        :param object value: value of item.
        """

        self.code = code
        self.itype = itype
        self.value = value
