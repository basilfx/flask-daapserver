import sys
import ctypes
import uuid

def generate_persistent_id():
    """
    Generate a persistent ID. This ID is used in the DAAP protocol to uniquely
    identify objects when they are created.
    """

    return ctypes.c_long(uuid.uuid1().int >> 64).value

def parse_byte_range(byte_range, min_byte=0, max_byte=sys.maxint):
    """
    Parse and validate a byte range. A byte range is a tuple of (begin, end)
    indices. `begin' should be smaller than `end', and both should fall within
    the `min_byte' and `max_byte'.

    In case of a violation, a ValueError is raised.
    """

    if not byte_range:
        return min_byte, max_byte

    begin = byte_range[0] or min_byte
    end = byte_range[1] or max_byte

    if end < begin:
        raise ValueError("End before begin")

    if begin < min_byte:
        raise ValueError("Begin smaller than min")

    if end > max_byte:
        raise ValueError("End larger than max")

    return begin, end

def to_tree(instance, *children):
    yield repr(instance)

    # Iterate trough each instance child collection
    for i, item in enumerate(children):
        name, child = item
        lines = 0

        yield "|"
        yield "+---" + name

        if i != len(children) - 1:
            a = "|"
        else:
            a = " "

        # Iterate trough all values of collection of child
        for j, item in enumerate(child.itervalues()):
            if j != len(child) - 1:
                b = "|"
            else:
                b = " "

            if j == 0:
                yield a + "   |"

            # Append prefix to each line
            for k, line in enumerate(item.to_tree()):
                lines += 1

                if k == 0:
                    yield a + "   +---" + line
                else:
                    yield a + "   " + b + "   " + line

        # Add extra space if required
        if len(children) > 1 and i == len(children) - 1 and lines > 1:
            yield a

class Mapping(object):

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def iterkeys(self):
        return iter(self)

    def itervalues(self):
        for key in self:
            yield self[key]

    def iteritems(self):
        for key in self:
            yield (key, self[key])

    def keys(self):
        return list(self)

    def items(self):
        return [(key, self[key]) for key in self]

    def values(self):
        return [self[key] for key in self]

    # Mappings are not hashable by default, but subclasses can change this
    __hash__ = None