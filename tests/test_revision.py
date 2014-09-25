from daapserver.revision import TreeRevisionStorage
from daapserver.revision import NOOP, ADD, EDIT, DELETE

import unittest

class TreeRevisionStorageTest(unittest.TestCase):
    """
    Tests for tree revision storage.
    """

    def test_last_operation(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.set("parent", "child_one", 2)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, EDIT)

        storage.delete("parent", "child_one")

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)

        self.assertEqual(storage.get("parent", revision=1), set([1]), )
        self.assertEqual(storage.get("parent", revision=2), set([2]))
        self.assertEqual(storage.get("parent", revision=3), set([]))

    def test_delete_missing(self):
        storage = TreeRevisionStorage()

        with self.assertRaises(KeyError):
            storage.delete("parent")

        with self.assertRaises(KeyError):
            storage.delete("parent", "child")

    def test_delete_double(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.delete("parent", "child_one")

        with self.assertRaises(KeyError):
            storage.delete("parent", "child_one")

        storage.delete("parent")

    def test_delete_double_parent(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.delete("parent")

        with self.assertRaises(KeyError):
            storage.delete("parent")

        with self.assertRaises(KeyError):
            storage.delete("parent", "child_one")

    def test_clear(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.set("parent", "child_two", 2)
        storage.set("parent", "child_three", 3)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.clear("parent")

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([]))

        storage.clear("parent")

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([]))

        self.assertEqual(storage.get("parent", revision=1), set([1, 2, 3]))
        self.assertEqual(storage.get("parent", revision=2), set([]))

    def test_clear_deleted(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.set("parent", "child_two", 2)
        storage.set("parent", "child_three", 3)

        storage.delete("parent")

        with self.assertRaises(KeyError):
            storage.clear("parent")

    def test_get_aligned(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)

        storage.set("dummy", "dummy_one", "a")
        storage.delete("dummy", "dummy_one")
        storage.set("dummy", "dummy_two", "b")
        storage.delete("dummy", "dummy_two")
        storage.set("dummy", "dummy_three", "c")
        storage.delete("dummy", "dummy_three")

        self.assertEqual(storage.revision, 6)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([1]))

        storage.set("parent", "child_one", 2)

        self.assertEqual(storage.revision, 7)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get("parent"), set([2]))

        self.assertEqual(storage.get("parent", revision=1), set([1]))
        self.assertEqual(storage.get("parent", revision=2), set([1]))
        self.assertEqual(storage.get("parent", revision=3), set([1]))
        self.assertEqual(storage.get("parent", revision=4), set([1]))
        self.assertEqual(storage.get("parent", revision=5), set([1]))
        self.assertEqual(storage.get("parent", revision=6), set([1]))
        self.assertEqual(storage.get("parent", revision=7), set([2]))

        storage.set("dummy", "dummy_one", "a")
        storage.delete("dummy", "dummy_one")
        storage.set("dummy", "dummy_two", "b")
        storage.delete("dummy", "dummy_two")
        storage.set("dummy", "dummy_three", "c")
        storage.delete("dummy", "dummy_three")

        self.assertEqual(storage.revision, 13)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([2]))

        storage.delete("parent", "child_one")

        self.assertEqual(storage.revision, 13)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([]))

        self.assertEqual(storage.get("parent", revision=7), set([2]))
        self.assertEqual(storage.get("parent", revision=8), set([2]))
        self.assertEqual(storage.get("parent", revision=9), set([2]))
        self.assertEqual(storage.get("parent", revision=10), set([2]))
        self.assertEqual(storage.get("parent", revision=11), set([2]))
        self.assertEqual(storage.get("parent", revision=12), set([2]))
        self.assertEqual(storage.get("parent", revision=13), set([]))

        self.assertEqual(storage.get("parent", "child_one", revision=6), 1)
        self.assertEqual(storage.get("parent", "child_one", revision=7), 2)
        self.assertEqual(storage.get("parent", "child_one", revision=8), 2)

        with self.assertRaises(KeyError):
            storage.get("parent", "child_one", revision=13)

    def test_get_miss(self):
        storage = TreeRevisionStorage()

        with self.assertRaises(KeyError):
            storage.get("parent")

        with self.assertRaises(KeyError):
            storage.get("parent", "child")

    def test_basic(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.set("parent", "child_two", 2)
        storage.set("parent", "child_three", 3)

        self.assertEqual(storage.revision, 1)
        self.assertEqual(storage.last_operation, ADD)
        self.assertEqual(storage.get("parent", "child_one"), 1)
        self.assertEqual(storage.get("parent", "child_two"), 2)
        self.assertEqual(storage.get("parent", "child_three"), 3)
        self.assertEqual(storage.get("parent"), set([1, 2, 3]))

        storage.delete("parent", "child_one")

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent"), set([2, 3]))

        storage.delete("parent")

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent", revision=1), set([1, 2, 3]))

        with self.assertRaises(KeyError):
            storage.get("parent")

        with self.assertRaises(KeyError):
            storage.get("parent", revision=2)

        with self.assertRaises(KeyError):
            storage.get("parent", revision=3)

    def test_duplicate_keys(self):
        storage = TreeRevisionStorage()

        storage.set("parent_one", "child_one", "1")
        storage.set("parent_two", "child_one", 1)

        self.assertNotEqual(storage.get("parent_one", "child_one"), storage.get("parent_two", "child_one"))

    def test_clean(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.set("parent", "child_one", 2)
        storage.delete("parent", "child_one")

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)
        self.assertEqual(storage.get("parent", revision=1), set([1]))
        self.assertEqual(storage.get("parent", revision=2), set([2]))
        self.assertEqual(storage.get("parent", revision=3), set([]))

        storage.clean(up_to_including_revision=1)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)

        with self.assertRaises(KeyError):
            storage.get("parent", revision=1)
        self.assertEqual(storage.get("parent", revision=2), set([2]))
        self.assertEqual(storage.get("parent", revision=3), set([]))

        storage.clean()

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, DELETE)

        with self.assertRaises(KeyError):
            storage.get("parent", revision=1)
            storage.get("parent", revision=2)
        self.assertEqual(storage.get("parent", revision=3), set([]))

    def test_commit(self):
        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.set("parent", "child_one", 2)
        storage.set("parent", "child_one", 3)

        self.assertEqual(storage.revision, 2)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get("parent", revision=1), set([1]))
        self.assertEqual(storage.get("parent", revision=2), set([3]))

        storage = TreeRevisionStorage()

        storage.set("parent", "child_one", 1)
        storage.commit()
        storage.set("parent", "child_one", 2)
        storage.commit()
        storage.set("parent", "child_one", 3)

        self.assertEqual(storage.revision, 3)
        self.assertEqual(storage.last_operation, EDIT)
        self.assertEqual(storage.get("parent", revision=1), set([1]))
        self.assertEqual(storage.get("parent", revision=2), set([2]))
        self.assertEqual(storage.get("parent", revision=3), set([3]))

        storage = TreeRevisionStorage()