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

from daapserver.daap_data import dmapDataTypes, dmapNames, \
    dmapReverseDataTypes, dmapCodeTypes

import struct

__all__ = ["DAAPObject", "SpeedyDAAPObject"]


class DAAPObject(object):
    """
    Represent a DAAP data object.
    """

    __slots__ = ("code", "value", "itype")

    def __init__(self, code=None, value=None):
        if code:
            try:
                self.code = dmapNames[code]
            except KeyError:
                raise ValueError("Unexpected code '%s'" % code)

            self.itype = dmapCodeTypes[self.code][1]
            self.value = value

    def to_tree(self, level=0):
        yield "\t" * level + "%s (%s)\t%s\t%s\n" % (
            dmapCodeTypes[self.code][0], self.code,
            dmapReverseDataTypes[self.itype], self.value)

        if self.itype == 12:
            for obj in self.value:
                yield obj.to_tree(level + 1)

    def encode(self):
        # Generate DMAP tagged data format. Find out what type of object
        # this is
        if self.itype == 12:
            # Object is a container. This means the items within `self.value'
            # are inspected.
            value = bytearray()
            for item in self.value:
                value.extend(item.encode())

            # Get the length of the data
            length = len(value)

            # Pack data: 4 byte code, 4 byte length, length bytes of value
            try:
                return struct.pack(
                    "!4sI%ds" % length, self.code, length, str(value))
            except struct.error as e:
                raise ValueError(
                    "Error while packing code '%s' ('%s'): %s" %
                    (self.code, dmapCodeTypes[self.code][0], e))
        else:
            # Determine the packing
            if self.itype == 11:
                value = struct.pack("!HH", *self.value.split("."))
                packing = "4s"
                length = 4
            elif self.itype == 7:
                packing = "q"
                length = 8
            elif self.itype == 8:
                packing = "Q"
                length = 8
            elif self.itype == 5:
                if type(self.value) == str and len(self.value) <= 4:
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
                if type(self.value) == unicode:
                    value = self.value.encode("utf-8")

                length = len(value)
                packing = "%ss" % length
            else:
                raise ValueError(
                    "Unexpected type %d" % dmapReverseDataTypes[self.itype])

            # Pack data: 4 characters for the code, 4 bytes for the length
            # and length bytes for the value
            try:
                return struct.pack(
                    "!4sI%s" % packing, self.code, length, self.value)
            except struct.error as e:
                raise ValueError(
                    "Error while packing code '%s' ('%s'): %s" % (
                        self.code, dmapCodeTypes[self.code][0], e))

    def decode(self, stream):
        # Read 4 bytes for the code and 4 bytes for the length of the
        # objects data.
        data = stream.read(8)

        try:
            self.code, length = struct.unpack("!4sI", data)
        except struct.error as e:
            raise ValueError("Error while unpacking code: %s" % e)

        # Now we need to find out what type of object it is
        try:
            self.itype = dmapCodeTypes[self.code][1]
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
            code = stream.read(length)

            if self.itype == 7:
                value = struct.unpack("!q", code)[0]
            elif self.itype == 8:
                value = struct.unpack("!Q", code)[0]
            elif self.itype == 5:
                value = struct.unpack("!i", code)[0]
            elif self.itype == 6:
                value = struct.unpack("!I", code)[0]
            elif self.itype == 3:
                value = struct.unpack("!h", code)[0]
            elif self.itype == 4:
                value = struct.unpack("!H", code)[0]
            elif self.itype == 1:
                value = struct.unpack("!b", code)[0]
            elif self.itype == 2:
                value = struct.unpack("!B", code)[0]
            elif self.itype == 11:
                value = float("%s.%s" % struct.unpack("!HH", code))
            elif self.itype == 10:
                value = struct.unpack("!I", code)[0]
            elif self.itype == 9:
                # The object is a string. The string's length is important.
                try:
                    value = unicode(struct.unpack(
                        "!%ss" % length, code)[0], "utf-8")
                except UnicodeDecodeError:
                    value = unicode(struct.unpack(
                        "!%ss" % length, code)[0], "latin-1")
            else:
                raise ValueError(
                    "Unexpected type '%s'" % dmapDataTypes[self.itype])

            self.value = value


class SpeedyDAAPObject(DAAPObject):
    """
    Extension of DAAPObject that directly sets the values. This does not check
    the values.
    """

    __slots__ = DAAPObject.__slots__

    def __init__(self, code, itype, value):
        self.code = code
        self.itype = itype
        self.value = value
