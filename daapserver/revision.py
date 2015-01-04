from daapserver import constants

import collections


class TreeRevisionStorage(object):
    """
    Key-value storage with revisioning. Keys are integer-only, and child keys
    are limited to 24 bits.
    """

    def __init__(self):
        self.storage = collections.defaultdict(list)

        self.revision = 1
        self.last_operation = constants.NOOP

    def get_index(self, key, revision):
        """
        Search for the index of an item where the revision is equal or less
        than given. For instance, having revisions [1, 5, 6], searching for 1-4
        yields 0, 5 yields 2 and 6 yields 2.
        """

        low = 0
        high = len(self.storage[key])

        # Perform right bisect
        while low < high:
            middle = (low + high) // 2

            if (self.storage[key][middle][0] >> 4) > revision:
                high = middle
            else:
                low = middle + 1

        return low

    def commit(self):
        """
        Make sure next operation causes a revision increment. This is useful
        for set operations, since two sequential edits don't increment.
        """
        self.last_operation = constants.NOOP

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

                if not items[start - 1][0] & constants.DELETE:
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

        key = (parent_key << 8) + constants.KEY

        if self.storage[key]:
            if self.storage[key][-1][0] & constants.DELETE:
                raise KeyError("Item marked as deleted: %s" % parent_key)
        else:
            raise KeyError("Item not found: %s" % parent_key)

        if self.last_operation != constants.DELETE:
            self.last_operation = constants.DELETE
            self.revision += 1

        # Delete children and update references
        for child_key in self.storage[key][-1][1]:
            self.storage[(parent_key << 24) + child_key].append(
                (self.revision << 4 | constants.DELETE, None))

        if (self.storage[key][-1][0] >> 4) == self.revision:
            self.storage[key][-1] = (
                self.revision << 4 | constants.EDIT, set())
        else:
            self.storage[key].append(
                (self.revision << 4 | constants.EDIT, set()))

    def info(self, parent_key, child_key=None, revision=None):
        """
        Return the revision number and the last operation that is in the
        history of a given `child_key' of a `parent_key', or just `parent_key'.
        """

        # Build lookup key
        key = (parent_key << 8) + constants.KEY \
            if child_key is None else (parent_key << 24) + child_key

        # Find item
        try:
            if revision is None:
                item = self.storage[key][-1]
            else:
                item = self.storage[key][self.get_index(key, revision) - 1]
        except IndexError:
            # Item not found, e.g. no revision history
            return None

        # Return the revision and last operation
        return item[0] >> 4, item[0] & 0x0F

    def load(self, parent_key, iterable):
        """
        Load a given iterable of key-value items into the storage, without
        revisioning. This method assumes that the parent container is empty
        """

        key = (parent_key << 8) + constants.KEY

        # Make sure parent exists
        if not self.storage[key]:
            self.storage[key].append(
                (self.revision << 4 | constants.EDIT, set()))

        # Add each key to the set
        keys = self.storage[key][-1][1]

        for original_child_key, child_value in iterable:
            child_key = (parent_key << 24) + original_child_key

            self.storage[child_key].append(
                (self.revision << 4 | constants.ADD, child_value))
            keys.add(original_child_key)

    def get(self, parent_key, child_key=None, revision=None):
        """
        Get a given item, optionally at a specific revision number. If
        `child_key' is None and `keys' is True, the keys stored under
        `parent_key' will be returned.
        """

        # Build lookup key
        key = (parent_key << 8) + constants.KEY \
            if child_key is None else (parent_key << 24) + child_key

        # Check if there are any items stored.
        if not self.storage[key]:
            raise KeyError("No item stored for key: %s" % key)

        # Optimize for no revision, since it is the last one in the list
        if revision is None:
            item = self.storage[key][-1]
        else:
            if revision > self.revision:
                raise KeyError(
                    "Requested revision %d greater than current revision %d" %
                    (revision, self.revision))
            elif (self.storage[key][0][0] >> 4) > revision:
                raise KeyError(
                    "Requested revision %d is lower than first element "
                    "revision %d" % (revision, self.storage[key][0][0] >> 4))

            # Find item with binary search
            item = self.storage[key][self.get_index(key, revision) - 1]

        # Check if items is marked as deleted
        if item[0] & constants.DELETE:
            raise KeyError("Item marked as deleted: %s" % key)

        return item[1]

    def delete(self, parent_key, child_key=None):
        """
        Delete a given item.
        """

        key = (parent_key << 8) + constants.KEY

        # Remove all items individually
        if child_key is None:
            if self.storage[key]:
                if self.storage[key][-1][0] & constants.DELETE:
                    raise KeyError("Item marked as deleted: %s" % parent_key)
            else:
                raise KeyError("Item not found: %s" % parent_key)

            if self.last_operation != constants.DELETE:
                self.last_operation = constants.DELETE
                self.revision += 1

            # Delete children and update references
            for child_key in self.storage[key][-1][1]:
                self.storage[(parent_key << 24) + child_key].append(
                    (self.revision << 4 | constants.DELETE, None))

            if (self.storage[key][-1][0] >> 4) == self.revision:
                self.storage[key][-1] = (
                    self.revision << 4 | constants.DELETE, None)
            else:
                self.storage[key].append(
                    (self.revision << 4 | constants.DELETE, None))
        else:
            original_child_key = child_key
            child_key = (parent_key << 24) + child_key

            if self.storage[child_key]:
                if self.storage[child_key][-1][0] & constants.DELETE:
                    raise KeyError("Item marked as deleted: %s" % child_key)
            else:
                raise KeyError("Item not found: %s" % child_key)

            if self.last_operation != constants.DELETE:
                self.last_operation = constants.DELETE
                self.revision += 1

            # Copy references
            if (self.storage[key][-1][0] >> 4) != self.revision:
                self.storage[key].append(
                    (self.revision << 4 | constants.EDIT,
                        self.storage[key][-1][1].copy()))

            # Delete child and update references
            self.storage[key][-1][1].remove(original_child_key)
            self.storage[child_key].append(
                (self.revision << 4 | constants.DELETE, None))

    def set(self, parent_key, child_key, child_value):
        """
        Add or edit an item.
        """

        key = (parent_key << 8) + constants.KEY

        original_child_key = child_key
        child_key = (parent_key << 24) + child_key

        # Check for existing item
        if not self.storage[child_key] or \
                self.storage[child_key][-1][0] & constants.DELETE:
            operation = constants.ADD
        else:
            operation = constants.EDIT

        # Increment revision
        if self.last_operation != operation:
            self.last_operation = operation
            self.revision += 1
            new_revision = True
        else:
            new_revision = False

        # Create or copy references
        if self.storage[key]:
            last_revision = (self.storage[key][-1][0] >> 4)

            if new_revision or self.revision != last_revision:
                self.storage[key].append(
                    (self.revision << 4 | constants.EDIT,
                        self.storage[key][-1][1].copy()))
        else:
            self.storage[key].append(
                (self.revision << 4 | constants.EDIT, set()))

        # Set item and update references
        if operation == constants.ADD:
            self.storage[key][-1][1].add(original_child_key)

        self.storage[child_key].append(
            (self.revision << 4 | operation, child_value))
