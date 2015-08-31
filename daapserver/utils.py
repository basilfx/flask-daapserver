import sys
import uuid
import ctypes


def diff(new, old):
    """
    Compute the difference in items of two revisioned collections. If only
    `new' is specified, it is assumed it is not an update. If both are set,
    the removed items are returned first. Otherwise, the updated and edited
    ones are returned.

    :param set new: Set of new objects
    :param set old: Set of old objects
    :return: A tuple consisting of `(added, removed, is_update)`.
    :rtype: tuple
    """

    if old is not None:
        is_update = True

        removed = set(new.removed(old))
        updated = set(new.updated(old))
    else:
        is_update = False

        updated = new
        removed = set()

    return updated, removed, is_update


def generate_persistent_id():
    """
    Generate a persistent ID. This ID is used in the DAAP protocol to uniquely
    identify objects when they are created.

    :return: A 64-bit random integer
    :rtype: int
    """

    return ctypes.c_long(uuid.uuid1().int >> 64).value


def parse_byte_range(byte_range, min_byte=0, max_byte=sys.maxint):
    """
    Parse and validate a byte range. A byte range is a tuple of (begin, end)
    indices. `begin' should be smaller than `end', and both should fall within
    the `min_byte' and `max_byte'.

    In case of a violation, a `ValueError` is raised.
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
    Generate tree structure of an instance, and its children. This method
    yields its results, instead of returning them.
    """

    # Yield representation of self
    yield unicode(instance)

    # Iterate trough each instance child collection
    for i, child in enumerate(children):
        lines = 0

        yield "|"
        yield "+---" + unicode(child)

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


def invoke_hooks(hooks, name, *args, **kwargs):
    """
    Invoke one or more hooks that have been registered under `name'. Additional
    arguments and keyword arguments can be provided.

    There is no exception catching, so if a hook fails, it will disrupt the
    chain and/or rest of program.
    """

    callbacks = hooks.get(name, [])

    for callback in callbacks:
        callback(*args, **kwargs)
