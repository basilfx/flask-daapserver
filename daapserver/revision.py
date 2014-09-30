import collections
import unittest

NOOP = -1
ADD = 1
EDIT = 2
DELETE = 4

VALUE = 1
KEY = 2

class TreeRevisionStorage(object):
    """
    Key-value storage with revisioning.
    """

    def __init__(self):
        self.storage = collections.defaultdict(list)

        self.revision = 0
        self.last_operation = NOOP

    def get_index(self, key, revision):
        """
        Search for the index of an item where the revision is equal or less than
        given. For instance, having revisions [1, 5, 6], searching for 1-4
        yields 0, 5 yields 2 and 6 yields 2.
        """

        low = 0
        high = len(self.storage[key])

        # Perform right bisect
        while low < high:
            middle = (low + high) // 2

            if self.storage[key][middle][0] > revision:
                high = middle
            else:
                low = middle + 1

        return low

    def commit(self):
        """
        Make sure next operation causes a revision increment. This is useful for
        set operations, since two sequential edits don't increment.
        """
        self.last_operation = NOOP

    def clean(self, up_to_revision=None):
        """
        Clean all revision history up the given revision, or up to to the
        current revision.
        """

        # Take current revision minus one if none specified.
        if up_to_revision is None:
            up_to_revision = self.revision - 1

        # Cleanup old revision items. Iterates over every key.
        for key, items in self.storage.iteritems():
            if items:
                start = self.get_index(key, up_to_revision)

                if items[start - 1][1] != DELETE:
                    start -= 1

                if start >= 0:
                    items[:] = items[start:]

        # Commit after finishing, so next operation will certainly not affect
        # the current revision.
        self.commit()

    def clear(self, parent_key):
        """
        Clear a certain parent, opposed to delete, which will also delete the
        parent.
        """

        if self.storage[(KEY, parent_key)]:
            if self.storage[(KEY, parent_key)][-1][1] == DELETE:
                raise KeyError("Item marked as deleted: %s" % (parent_key, ))
        else:
            raise KeyError("Item not found: %s" % (parent_key, ))

        if self.last_operation != DELETE:
            self.last_operation = DELETE
            self.revision += 1

        # Delete children and update references
        for child_key in self.storage[(KEY, parent_key)][-1][2]:
            self.storage[(parent_key, child_key)].append(
                (self.revision, DELETE, None))

        if self.storage[(VALUE, parent_key)][-1][0] == self.revision:
            self.storage[(VALUE, parent_key)][-1] = \
                (self.revision, EDIT, set())
            self.storage[(KEY, parent_key)][-1] = \
                (self.revision, EDIT, set())
        else:
            self.storage[(VALUE, parent_key)].append(
                (self.revision, EDIT, set()))
            self.storage[(KEY, parent_key)].append(
                (self.revision, EDIT, set()))

    def info(self, parent_key, child_key, revision):
        """
        Return the revision number and the last operation that is in the
        history of a given `child_key' of a `parent_key'.
        """

        key = (parent_key, child_key)

        # Find item
        item = self.storage[key][self.get_index(key, revision) - 1]

        # Return the revision and last operation
        return item[0], item[1]

    def get(self, parent_key, child_key=None, revision=None, keys=False):
        """
        Get a given item, optionally at a specific revision number. If
        `child_key' is None and `keys' is True, the keys stored under
        `parent_key' will be returned.
        """

        # Build lookup key
        key = (KEY if keys else VALUE, parent_key) \
            if child_key is None else (parent_key, child_key)

        # Check if there are any items stored.
        if not self.storage[key]:
            raise KeyError("No item stored for key: %s" % (key, ))

        # Optimize for no revision, since it is the last one in the list
        if revision is None:
            item = self.storage[key][-1]
        else:
            if revision > self.revision:
                raise KeyError("Requested revision %d greater than current " \
                    "revision %d" % (revision, self.revision))
            elif self.storage[key][0][0] > revision:
                raise KeyError("Requested revision %d lower than first " \
                    "element revision %d" % (revision, self.storage[key][0][0]))

            # Find item with binary search
            item = self.storage[key][self.get_index(key, revision) - 1]

        # Check if items is marked as deleted
        if item[1] == DELETE:
            raise KeyError("Item marked as deleted: %s" % (key, ))

        return item[2]

    def delete(self, parent_key, child_key=None):
        """
        Delete a given item.
        """

        # Remove all items individually
        if child_key is None:
            if self.storage[(KEY, parent_key)]:
                if self.storage[(KEY, parent_key)][-1][1] == DELETE:
                    raise KeyError("Item marked as deleted: %s" %
                        (parent_key, ))
            else:
                raise KeyError("Item not found: %s" % (parent_key, ))

            if self.last_operation != DELETE:
                self.last_operation = DELETE
                self.revision += 1

            # Delete children and update references
            for child_key in self.storage[(KEY, parent_key)][-1][2]:
                self.storage[(parent_key, child_key)].append(
                    (self.revision, DELETE, None))

            if self.storage[(VALUE, parent_key)][-1][0] == self.revision:
                self.storage[(VALUE, parent_key)][-1] = \
                    (self.revision, DELETE, None)
                self.storage[(KEY, parent_key)][-1] = \
                    (self.revision, DELETE, None)
            else:
                self.storage[(VALUE, parent_key)].append(
                    (self.revision, DELETE, None))
                self.storage[(KEY, parent_key)].append(
                    (self.revision, DELETE, None))
        else:
            if self.storage[(parent_key, child_key)]:
                if self.storage[(parent_key, child_key)][-1][1] == DELETE:
                    raise KeyError("Item marked as deleted: %s" %
                        ((parent_key, child_key), ))
            else:
                raise KeyError("Item not found: %s" %
                    ((parent_key, child_key), ))

            if self.last_operation != DELETE:
                self.last_operation = DELETE
                self.revision += 1

            # Copy references
            if self.storage[(VALUE, parent_key)][-1][0] != self.revision:
                self.storage[(VALUE, parent_key)].append((self.revision, EDIT,
                    self.storage[(VALUE, parent_key)][-1][2].copy()))
                self.storage[(KEY, parent_key)].append((self.revision, EDIT,
                    self.storage[(KEY, parent_key)][-1][2].copy()))

            # Delete child and update references
            child_value = self.storage[(parent_key, child_key)][-1][2]

            self.storage[(VALUE, parent_key)][-1][2].remove(child_value)
            self.storage[(KEY, parent_key)][-1][2].remove(child_key)

            self.storage[(parent_key, child_key)].append(
                (self.revision, DELETE, None))

    def set(self, parent_key, child_key, child_value):
        """
        Add or edit an item.
        """

        # Check for existing item
        if (not self.storage[(parent_key, child_key)] or
            self.storage[(parent_key, child_key)][-1][1] == DELETE):
            operation = ADD
        else:
            operation = EDIT

        # Increment revision
        if self.last_operation != operation:
            self.last_operation = operation
            self.revision += 1
            new_revision = True
        else:
            new_revision = False

        # Create or copy references
        if self.storage[(KEY, parent_key)]:
            last_revision = self.storage[(KEY, parent_key)][-1][0]

            if new_revision or self.revision != last_revision:
                self.storage[(VALUE, parent_key)].append((self.revision, EDIT,
                    self.storage[(VALUE, parent_key)][-1][2].copy()))
                self.storage[(KEY, parent_key)].append((self.revision, EDIT,
                    self.storage[(KEY, parent_key)][-1][2].copy()))
        else:
            self.storage[(VALUE, parent_key)].append(
                (self.revision, EDIT, set()))
            self.storage[(KEY, parent_key)].append(
                (self.revision, EDIT, set()))

        # Set item and update references
        if operation == ADD:
            self.storage[(VALUE, parent_key)][-1][2].add(child_value)
            self.storage[(KEY, parent_key)][-1][2].add(child_key)
        elif operation == EDIT:
            old_child_value = self.storage[(parent_key, child_key)][-1][2]

            self.storage[(VALUE, parent_key)][-1][2].remove(old_child_value)
            self.storage[(VALUE, parent_key)][-1][2].add(child_value)

        self.storage[(parent_key, child_key)].append(
            (self.revision, operation, child_value))