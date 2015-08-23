# -*- coding: utf-8 -*-

from daapserver.collection import ImmutableCollection, LazyMutableCollection

import unittest
import collections


class MyItem(object):
    def __init__(self, id, registry):
        """"
        Construct a new item.
        """

        self.id = id
        self.registry = registry

        # Increment registry count
        self.registry[id] += 1

    def __repr__(self):
        """
        Self representation (for debugging).
        """

        return "MyItem(id=%d, python_id=%d)" % (self.id, id(self))


class MyLazyMutableCollection(LazyMutableCollection):

    def __init__(self):
        """
        Initialize a new lazy collection.
        """

        super(MyLazyMutableCollection, self).__init__(self)

        self.registry = collections.defaultdict(int)

    def count(self):
        """
        Basic count implementation.
        """

        return 5

    def load(self, item_ids=None):

        if self.busy:
            raise ValueError("Already busy")

        try:
            self.busy = True

            for item_id in (item_ids or range(5)):
                # Update an existing item
                if item_ids:
                    item = self.store.get(item_id)
                else:
                    item = MyItem(item_id, self.registry)

                # Add to store
                self.store.add(item.id, item)

                # Yield result
                self.iter_item = item
                yield item

                # Final actions after all items have been loaded
                if not item_ids:
                    self.ready = True

                    if self.pending_commit != -1:
                        revision = self.pending_commit
                        self.pending_commit = -1
                        self.commit(revision)

        finally:
            self.busy = False


class TestImmutableCollection(unittest.TestCase):
    """
    Test cases for `daapserver.collection.ImmutableCollection'.
    """

    def test_unicode_str_repr(self):
        """
        Test model to unicode, string and representation methods.
        """

        immutable_collection = ImmutableCollection(
            parent=u"Nörmally an öbject")

        for instance in [immutable_collection]:
            # Type checking
            self.assertTrue(type(unicode(instance)), unicode)
            self.assertTrue(type(str(instance)), str)
            self.assertTrue(type(repr(instance)), str)

            # String variant replaces non-ascii characters
            self.assertTrue(
                unicode(instance).encode("ascii", "replace") == str(instance))


class TestLazyMutableCollection(unittest.TestCase):
    """
    Test cases for `daapserver.collection.LazyMutableCollection'. It is
    implemented as `MyLazyMutableCollection' to provide the necessary `load'
    and `count' methods.
    """

    def setUp(self):
        """
        Setup a new collection.
        """
        self.collection = MyLazyMutableCollection()

    def test_busy(self):
        """
        Check if busy flag is True while loading and False after loading.
        """

        self.assertFalse(self.collection.busy)
        self.assertFalse(self.collection.ready)

        for item in self.collection:
            self.assertTrue(self.collection.busy)

        self.assertFalse(self.collection.busy)
        self.assertTrue(self.collection.ready)

    def test_count(self):
        """
        Check if count does not trigger a load event.
        """

        self.assertFalse(self.collection.ready)
        self.assertEqual(len(self.collection), 5)
        self.assertFalse(self.collection.ready)

        # Trigger a load event.
        list(self.collection)

        self.assertEqual(len(self.collection), 5)
        self.assertTrue(self.collection.ready)

    def test_modified_and_pending_commit(self):
        """
        Check if non-ready commit makes it a pending one, except if not
        modified.
        """

        self.assertFalse(self.collection.ready)
        self.assertFalse(self.collection.modified)
        self.assertEqual(self.collection.pending_commit, -1)

        # Commit, but nothing was modified, so it is safe to commit.
        self.collection.commit(2)

        self.assertFalse(self.collection.ready)
        self.assertFalse(self.collection.modified)
        self.assertEqual(self.collection.pending_commit, -1)

        # Add one item, which will make it modified.
        self.collection.add(MyItem(1, self.collection.registry))

        self.assertFalse(self.collection.ready)
        self.assertTrue(self.collection.modified)
        self.assertEqual(self.collection.pending_commit, -1)

        # Commit again, this time the collection is modified and commit will be
        # pended.
        self.collection.commit(3)

        self.assertFalse(self.collection.ready)
        self.assertTrue(self.collection.modified)
        self.assertEqual(self.collection.pending_commit, 3)

        # Load all keys, which will make it ready and commit
        keys = self.collection.keys()

        self.assertListEqual(keys, [0, 1, 2, 3, 4])
        self.assertTrue(self.collection.modified)
        self.assertTrue(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

        # Collection is ready, so next commit will not pend it.
        self.collection.commit(4)

        self.assertTrue(self.collection.modified)
        self.assertTrue(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

    def test_get_item(self):
        """
        Check if item retrieval makes collection ready and keeps it ready.
        """

        self.assertFalse(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

        # Get item
        item_a = self.collection[2]

        self.assertTrue(self.collection.ready)

        # Get item again
        item_b = self.collection[2]

        self.assertEqual(id(item_a), id(item_b))
        self.assertEqual(self.collection.registry[2], 1)

        # Commit collection
        self.collection.commit(3)

        self.assertTrue(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

        item_c = self.collection[2]

        self.assertEqual(id(item_a), id(item_c))
        self.assertEqual(self.collection.registry[2], 1)

    def test_update_remove_items(self):
        """
        Test if item is not re-created when updated (the old revision is
        reused).
        """

        # Ensure list ready
        list(self.collection)

        self.assertTrue(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

        self.collection.commit(3)

        self.assertTrue(self.collection.ready)
        self.assertEqual(self.collection.pending_commit, -1)

        self.collection.update_ids([2, 3])
        self.collection.commit(4)

        self.assertEqual(self.collection.registry[2], 1)
        self.assertEqual(self.collection.registry[3], 1)

        item_ids = list(self.collection(3).updated(self.collection(1)))
        self.assertListEqual(item_ids, [2, 3])

        self.collection.remove_ids([3, 4])
        self.collection.commit(5)

        self.assertListEqual(self.collection.keys(), [2, 1, 0])
        item_ids = list(self.collection(4).removed(self.collection(3)))
        self.assertListEqual(item_ids, [3, 4])
