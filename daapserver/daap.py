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

from daapserver.daap_data import *

import sys
import struct
import logging

__all__ = ['DAAPObject', 'DAAPParseCodeTypes']

logger = logging.getLogger(__name__)

def DAAPParseCodeTypes(treeroot):
    # The treeroot we are given should be a dmap.contentcodesresponse
    if treeroot.get_code_name() == 'dmap.contentcodesresponse':
        raise ValueError("Cannot generate a dictionary from tree.")

    for obj in treeroot.value:
        # Each item should be either a status code, or a dictionary
        if obj.get_code_name() == 'dmap.status':
            pass
        elif obj.get_code_name() == 'dmap.dictionary':
            code, name, dtype = None, None, None

            # A dictionary object should contain three items:
            # a 'dmap.contentcodesnumber' the 4 letter content code
            # a 'dmap.contentcodesname' the name of the code
            # a 'dmap.contentcodestype' the type of the code
            for info in obj.value:
                if info.get_code_name() == 'dmap.contentcodesnumber':
                    code = info.value
                elif info.get_code_name() == 'dmap.contentcodesname':
                    name = info.value
                elif info.get_code_name() == 'dmap.contentcodestype':
                    try:
                        dtype = dmapDataTypes[info.value]
                    except:
                        logger.debug('Unknown data type %s for code %s, defaulting to s',
                            info.value, name)
                        dtype = 's'
                else:
                    raise ValueError('Unexpected code %s at level 2' %
                        info.get_code_name())

            if code and name and dtype:
                try:
                    dtype = dmapFudgeDataTypes[name]
                except KeyError:
                    pass

                dmapCodeTypes[code] = (name, dtype)
            else:
                logger.debug('Missing information, not adding entry')
        else:
            raise ValueError('Unexpected code %s at level 1' % info.get_code_name())

class DAAPObject(object):
    __slots__ = ["code", "value", "type", "itype"]

    def __init__(self, code=None, value=None):
        if code:
            try:
                self.code = dmapNames[code]
            except KeyError:
                raise ValueError("Unexpected code '%s'" % code)

            self.type = dmapCodeTypes[self.code][1]
            self.itype = dmapReverseDataTypes[self.type] # Integers are faster
            self.value = value

    def get_atom(self, code):
        """Returns an atom of the given code by searching 'contains' recursively.
        """

        if self.code == code:
            if self.type == 'c':
                return self
            else:
                return self.value

        # It's not us. check our children
        if self.type == 'c':
            for obj in self.value:
                value = obj.get_atom(code)

                if value is not None:
                    return value

    def get_code_name(self):
        try:
            return dmapCodeTypes[self.code][0]
        except KeyError:
            pass

    def get_object_type(self):
        try:
            return dmapCodeTypes[self.code][1]
        except KeyError:
            pass

    def to_tree(self, level=0, out=sys.stdout):
        out.write('\t' * level + '%s (%s)\t%s\t%s\n' %
            (self.get_code_name(), self.code, self.type, self.value))

        if self.type =='c':
            for obj in self.value:
                obj.print_tree(level + 1)

    def encode(self):
        # Generate DMAP tagged data format. Find out what type of object this is
        if self.type == 'c':
            # Object is a container. This means the items within self.value are
            # inspected.
            value = bytearray()
            for item in self.value:
                value.extend(item.encode())

            # Get the length of the data
            length = len(value)

            # Pack data: 4 byte code, 4 byte length, length bytes of value
            try:
                return struct.pack('!4sI%ds' % length, self.code, length, str(value))
            except struct.error as e:
                raise ValueError("Error while packing code '%s' ('%s'): %s" %
                    (self.code, self.get_code_name(), e))
        else:
            # Determine the packing
            value = self.value

            if self.itype == 11:
                value = str(value).split('.')
                value = struct.pack('!HH', int(value[0]), int(value[1]))
                packing = "4s"
            elif self.itype == 7:
                packing = 'q'
            elif self.itype == 8:
                packing = 'Q'
            elif self.itype == 5:
                if type(value) == str and len(value) <= 4:
                    packing = '4s'
                else:
                    packing = 'i'
            elif self.itype == 6:
                packing = 'I'
            elif self.itype == 3:
                packing = 'h'
            elif self.itype == 4:
                packing = 'H'
            elif self.itype == 1:
                packing = 'b'
            elif self.itype == 2:
                packing = 'B'
            elif self.itype == 10:
                packing = 'I'
            elif self.itype == 9:
                if type(value) == unicode:
                    value = value.encode('utf-8')
                packing = '%ss' % len(value)
            else:
                raise ValueError('Unexpected type %d' % self.type)

            # Calculate the length of what we're packing
            length = struct.calcsize('!%s' % packing)

            # Pack data: 4 characters for the code, 4 bytes for the length and
            # length bytes for the value
            try:
                return struct.pack('!4sI%s' % (packing), self.code, length, value)
            except struct.error as e:
                raise ValueError("Error while packing code '%s' ('%s'): %s" %
                    (self.code, self.get_code_name(), e))

    def decode(self, stream):
        # Read 4 bytes for the code and 4 bytes for the length of the objects data
        data = stream.read(8)

        try:
            self.code, length = struct.unpack('!4sI', data)
        except struct.error as e:
            raise ValueError("Error while unpacking code: %s" % e)

        # Now we need to find out what type of object it is
        try:
            self.type = dmapCodeTypes[self.code][1]
            self.itype = dmapReverseDataTypes[self.type]
        except KeyError:
            raise ValueError("Unknown code '%s'" % self.code)

        if self.type == 'c':
            start_pos = stream.tell()
            self.value = []

            # The object is a container, we need to pass it it's length amount
            # of data for processessing
            eof = 0
            while stream.tell() < start_pos + length:
                obj = DAAPObject()
                self.value.append(obj)
                obj.decode(stream)
        else:
            # Not a container, we're a single atom. Read it.
            code = stream.read(length)

            if self.itype == 7:
                value = struct.unpack('!q', code)[0]
            elif self.itype == 8:
                value = struct.unpack('!Q', code)[0]
            elif self.itype == 5:
                value = struct.unpack('!i', code)[0]
            elif self.itype == 6:
                value = struct.unpack('!I', code)[0]
            elif self.itype == 3:
                value = struct.unpack('!h', code)[0]
            elif self.itype == 4:
                value = struct.unpack('!H', code)[0]
            elif self.itype == 1:
                value = struct.unpack('!b', code)[0]
            elif self.itype == 2:
                value = struct.unpack('!B', code)[0]
            elif self.itype == 11:
                value = float("%s.%s" % struct.unpack('!HH', code))
            elif self.itype == 10:
                value = struct.unpack('!I', code)[0]
            elif self.itype == 9:
                # The object is a string. The strings length is important.
                try:
                    value = unicode(struct.unpack('!%ss' % length, code)[0], 'utf-8')
                except UnicodeDecodeError:
                    value = unicode(struct.unpack('!%ss' % length, code)[0], 'latin-1')
            else:
                # Unknow data type.
                raise ValueError('Unexpected type %d' % self.type)

            self.value = value
