import sys
import uuid
import ctypes


def diff(new, old):
    """
    Compute the difference in items of two revisioned collections. If only
    `new' is specified, it is assumed it's not an update. If both are set,
    first the removed items are returned. Otherwise, the added and edited ones.
    """

    added = set()
    removed = set()

    # Take either added or removed, but not both
    if new and old:
        is_update = True
        removed = new.removed(old)

        if not removed:
            added = new.added(old) | new.edited(old)
    else:
        is_update = False
        added = new

    return added, removed, is_update


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
    """
    Generate tree structure of an instance, and its children. Each child item
    should be a (name, child) tuple, where name will cover all the children.

    This method yields it results instead of returning them.
    """

    # Yield representation of self
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
