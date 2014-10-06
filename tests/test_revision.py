from daapserver.revision import TreeRevisionStorage
from daapserver.revision import NOOP, ADD, EDIT, DELETE

import unittest

# Supporting integer keys only, we define constants to represent the keys here.
PARENT = 0x01
CHILD = 0x02
DUMMY = 0x03

PARENT_ONE = 0x10
PARENT_TWO = 0x20
PARENT_THREE = 0x30

CHILD_ONE = 0x30
CHILD_TWO = 0x40
CHILD_THREE = 0x50

DUMMY_ONE = 0x60
DUMMY_TWO = 0x70
DUMMY_THREE = 0x80

class TreeRevisionStorageTest(unittest.TestCase):
    """
    Tests for tree revision storage.
    """

    def test_last_operation(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.set(PARENT, CHILD_ONE, 2)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, EDIT)

        storage.delete(PARENT, CHILD_ONE)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)

        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=1), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 2)

        with self.assertRaises(KeyError):
            storage.get(PARENT, CHILD_ONE, revision=3)

    def test_delete_missing(self):
        storage = TreeRevisionStorage()

        with self.assertRaises(KeyError):
            storage.delete(PARENT)

        with self.assertRaises(KeyError):
            storage.delete(PARENT, CHILD)

    def test_delete_double(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.delete(PARENT, CHILD_ONE)

        with self.assertRaises(KeyError):
            storage.delete(PARENT, CHILD_ONE)

        storage.delete(PARENT)

    def test_delete_double_parent(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.delete(PARENT)

        with self.assertRaises(KeyError):
            storage.delete(PARENT)

        with self.assertRaises(KeyError):
            storage.delete(PARENT, CHILD_ONE)

    def test_clear(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.set(PARENT, CHILD_TWO, 2)
        storage.set(PARENT, CHILD_THREE, 3)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.clear(PARENT)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT), set([]))

        storage.clear(PARENT)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT), set([]))

        self.assertEqual(storage.get(PARENT, revision=1),
            set([CHILD_ONE, CHILD_TWO, CHILD_THREE]))
        self.assertEqual(storage.get(PARENT, revision=2), set([]))

    def test_clear_deleted(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.set(PARENT, CHILD_TWO, 2)
        storage.set(PARENT, CHILD_THREE, 3)

        storage.delete(PARENT)

        with self.assertRaises(KeyError):
            storage.clear(PARENT)

    def test_get_aligned(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.set(DUMMY, DUMMY_ONE, "a")
        storage.delete(DUMMY, DUMMY_ONE)
        storage.set(DUMMY, DUMMY_TWO, "b")
        storage.delete(DUMMY, DUMMY_TWO)
        storage.set(DUMMY, DUMMY_THREE, "c")
        storage.delete(DUMMY, DUMMY_THREE)

        self.assertEqual(storage.revision, 6)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT), set([CHILD_ONE]))

        storage.set(PARENT, CHILD_ONE, 2)

        self.assertEqual(storage.revision, 7)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get(PARENT, CHILD_ONE), 2)

        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=1), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=3), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=4), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=5), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=6), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=7), 2)

        storage.set(DUMMY, DUMMY_ONE, "a")
        storage.delete(DUMMY, DUMMY_ONE)
        storage.set(DUMMY, DUMMY_TWO, "b")
        storage.delete(DUMMY, DUMMY_TWO)
        storage.set(DUMMY, DUMMY_THREE, "c")
        storage.delete(DUMMY, DUMMY_THREE)

        self.assertEqual(storage.revision, 13)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT, CHILD_ONE), 2)

        storage.delete(PARENT, CHILD_ONE)

        self.assertEqual(storage.revision, 13)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT), set([]))

        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=7), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=8), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=9), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=10), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=11), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=12), 2)
        self.assertEqual(storage.get(PARENT, revision=13), set([]))

        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=6), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=7), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=8), 2)

        with self.assertRaises(KeyError):
            storage.get(PARENT, CHILD_ONE, revision=13)

    def test_get_miss(self):
        storage = TreeRevisionStorage()

        with self.assertRaises(KeyError):
            storage.get(PARENT)

        with self.assertRaises(KeyError):
            storage.get(PARENT, CHILD)

    def test_basic(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.set(PARENT, CHILD_TWO, 2)
        storage.set(PARENT, CHILD_THREE, 3)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)
        self.assertEqual(storage.get(PARENT, CHILD_ONE), 1)
        self.assertEqual(storage.get(PARENT, CHILD_TWO), 2)
        self.assertEqual(storage.get(PARENT, CHILD_THREE), 3)
        self.assertEqual(storage.get(PARENT),
            set([CHILD_ONE, CHILD_TWO, CHILD_THREE]))

        storage.delete(PARENT, CHILD_ONE)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT), set([CHILD_TWO, CHILD_THREE]))

        storage.delete(PARENT)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT, revision=1),
            set([CHILD_ONE, CHILD_TWO, CHILD_THREE]))

        with self.assertRaises(KeyError):
            storage.get(PARENT)

        with self.assertRaises(KeyError):
            storage.get(PARENT, revision=2)

        with self.assertRaises(KeyError):
            storage.get(PARENT, revision=3)

    def test_duplicate_keys(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT_ONE, CHILD_ONE, "1")
        storage.set(PARENT_TWO, CHILD_ONE, 1)

        self.assertNotEqual(storage.get(PARENT_ONE, CHILD_ONE),
            storage.get(PARENT_TWO, CHILD_ONE))

    def test_clean(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.set(PARENT, CHILD_ONE, 2)
        storage.delete(PARENT, CHILD_ONE)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=1), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 2)
        with self.assertRaisesRegexp(KeyError, "Item marked .*"):
            storage.get(PARENT, CHILD_ONE, revision=3)

        storage.clean(up_to_revision=2)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, NOOP)

        with self.assertRaisesRegexp(KeyError, "Requested revision .*"):
            storage.get(PARENT, revision=1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 2)
        with self.assertRaisesRegexp(KeyError, "Item marked .*"):
            storage.get(PARENT, CHILD_ONE, revision=3)

        storage.clean()

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, NOOP)

        with self.assertRaisesRegexp(KeyError, "Requested revision .*"):
            storage.get(PARENT, CHILD_ONE, revision=1)
            storage.get(PARENT, CHILD_ONE, revision=2)
        with self.assertRaisesRegexp(KeyError, "Item marked .*"):
            storage.get(PARENT, CHILD_ONE, revision=3)
        self.assertEqual(storage.get(PARENT, revision=3), set([]))

    def test_commit(self):
        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.set(PARENT, CHILD_ONE, 2)
        storage.set(PARENT, CHILD_ONE, 3)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=1), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 3)

        storage = TreeRevisionStorage()

        storage.set(PARENT, CHILD_ONE, 1)
        storage.commit()
        storage.set(PARENT, CHILD_ONE, 2)
        storage.commit()
        storage.set(PARENT, CHILD_ONE, 3)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=1), 1)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=2), 2)
        self.assertEqual(storage.get(PARENT, CHILD_ONE, revision=3), 3)

        storage = TreeRevisionStorage()