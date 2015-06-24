from daapserver.revision import RevisionStore

import unittest


class TestRevisionStore(unittest.TestCase):

    def assertIterEqual(self, actual, expected):
        """
        Helper to cast actual iterator into a list.
        """

        self.assertListEqual(list(actual), expected)

    def setUp(self):
        """
        Initialize an empty revision store.
        """

        self.store = RevisionStore()

    def test_add(self):
        """
        Test basic add functionality.
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])

        self.store.add("A", "A2")
        self.store.add("D", "D1")

        self.assertIterEqual(self.store.iterate(), ["D1", "C1", "B1", "A2"])

    def test_remove(self):
        """
        Test basic remove functionality.
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])

        self.store.remove("A")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1"])

        self.store.remove("C")

        self.assertIterEqual(self.store.iterate(), ["B1"])

    def test_get(self):
        """
        Test basic get functionality
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertEqual(self.store.get("A"), "A1")
        self.assertEqual(self.store.get("A", revision=1), "A1")

        self.store.commit()
        self.store.add("A", "A2")

        self.assertEqual(self.store.get("A"), "A2")
        self.assertEqual(self.store.get("A", revision=2), "A2")
        self.assertEqual(self.store.get("A", revision=1), "A1")

        self.store.commit()
        self.store.remove("A")

        with self.assertRaises(KeyError):
            self.store.get("A")

        self.assertEqual(self.store.get("A", revision=2), "A2")
        self.assertEqual(self.store.get("A", revision=1), "A1")

    def test_get_fail(self):
        """
        Test edge cases for get functionality.
        """

        self.store.add("A", "A1")
        self.store.remove("A")

        with self.assertRaises(KeyError):
            self.store.get("A", revision=1)

    def test_commit(self):
        """
        Test commit and revision functionality.
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertEqual(self.store.revision, 1)
        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])

        self.store.commit()
        self.store.add("A", "A2")
        self.store.add("D", "D1")

        self.assertEqual(self.store.revision, 2)
        self.assertIterEqual(self.store.iterate(), ["D1", "C1", "B1", "A2"])
        self.assertIterEqual(
            self.store.iterate(revision=2), ["D1", "C1", "B1", "A2"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])

        self.store.commit()
        self.store.remove("A")
        self.store.remove("C")

        self.assertEqual(self.store.revision, 3)
        self.assertIterEqual(self.store.iterate(), ["D1", "B1"])
        self.assertIterEqual(self.store.iterate(revision=3), ["D1", "B1"])
        self.assertIterEqual(
            self.store.iterate(revision=2), ["D1", "C1", "B1", "A2"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])

    def test_iterate(self):
        """
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])
        self.assertIterEqual(
            self.store.iterate(revision=-1), ["C1", "B1", "A1"])

        with self.assertRaises(ValueError):
            for _ in self.store.iterate(revision=2):
                pass

    def test_clean(self):
        """
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])

        self.store.commit()
        self.store.remove("A")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1"])
        self.assertIterEqual(self.store.iterate(revision=2), ["C1", "B1"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])

        self.store.commit()
        self.store.remove("C")

        self.assertIterEqual(self.store.iterate(), ["B1"])
        self.assertIterEqual(self.store.iterate(revision=3), ["B1"])
        self.assertIterEqual(self.store.iterate(revision=2), ["C1", "B1"])
        self.assertIterEqual(
            self.store.iterate(revision=1), ["C1", "B1", "A1"])

        self.store.clean(revision=2)

        self.assertIterEqual(self.store.iterate(), ["B1"])
        self.assertIterEqual(self.store.iterate(revision=3), ["B1"])
        self.assertIterEqual(self.store.iterate(revision=2), ["C1", "B1"])

        with self.assertRaises(ValueError):
            for _ in self.store.iterate(revision=1):
                pass

        self.store.clean()

        self.assertIterEqual(self.store.iterate(), ["B1"])
        self.assertIterEqual(self.store.iterate(revision=3), ["B1"])

        with self.assertRaises(ValueError):
            for _ in self.store.iterate(revision=2):
                pass

    def test_diff(self):
        """
        Test diff functionality (1).
        """

        self.store.commit()
        self.store.add("A", "A2")
        self.store.commit()
        self.store.remove("A")

        self.assertIterEqual(self.store.diff(3, 1), [("A", 1)])
        self.assertIterEqual(self.store.diff(1, 3), [("A", -1)])

        self.assertIterEqual(self.store.diff(2, 1), [("A", 1)])
        self.assertIterEqual(self.store.diff(1, 2), [("A", -1)])

        self.assertIterEqual(self.store.diff(3, 2), [("A", -1)])
        self.assertIterEqual(self.store.diff(2, 3), [("A", 1)])

    def test_diff2(self):
        """
        Test diff functionality (2).
        """

        self.store.commit()
        self.store.add("A", "A2")
        self.store.commit()
        self.store.remove("A")
        self.store.commit()
        self.store.add("B", "B4")
        self.store.commit()
        self.store.add("C", "C5")
        self.store.commit()
        self.store.remove("B")

        self.assertIterEqual(self.store.diff(6, 5), [("B", -1)])
        self.assertIterEqual(self.store.diff(5, 6), [("B", 1)])

    def test_diff3(self):
        """
        Test diff functionality (3).
        """

        self.store.commit()
        self.store.add("A", "A2")
        self.store.commit()
        self.store.add("B", "B3")
        self.store.commit()
        self.store.add("C", "C4")

        self.assertIterEqual(self.store.diff(4, 3), [("C", 1)])
        self.assertIterEqual(self.store.diff(3, 4), [("C", -1)])

    def test_diff4(self):
        """
        Test diff functionality (4).
        """

        self.store.commit()
        self.store.add("A", "A2.1")
        self.store.add("A", "A2.2")
        self.store.commit()
        self.store.remove("A")
        self.store.commit()
        self.store.add("A", "A4")
        self.store.commit()
        self.store.remove("A")
        self.store.commit()
        self.store.add("A", "A6")
        self.store.commit()
        self.store.commit()
        self.store.add("A", "A8")

        self.assertIterEqual(self.store.diff(8, 7), [("A", 0)])
        self.assertIterEqual(self.store.diff(8, 6), [("A", 0)])
        self.assertIterEqual(self.store.diff(8, 5), [("A", 1)])
        self.assertIterEqual(self.store.diff(8, 4), [("A", 0)])
        self.assertIterEqual(self.store.diff(8, 3), [("A", 1)])
        self.assertIterEqual(self.store.diff(8, 2), [("A", 0)])
        self.assertIterEqual(self.store.diff(8, 1), [("A", 1)])

        self.assertIterEqual(self.store.diff(7, 8), [("A", 0)])
        self.assertIterEqual(self.store.diff(6, 8), [("A", 0)])
        self.assertIterEqual(self.store.diff(5, 8), [("A", -1)])
        self.assertIterEqual(self.store.diff(4, 8), [("A", 0)])
        self.assertIterEqual(self.store.diff(3, 8), [("A", -1)])
        self.assertIterEqual(self.store.diff(2, 8), [("A", 0)])
        self.assertIterEqual(self.store.diff(1, 8), [("A", -1)])

        self.assertIterEqual(self.store.diff(5, 2), [("A", -1)])
        self.assertIterEqual(self.store.diff(2, 5), [("A", 1)])

        self.assertIterEqual(self.store.diff(8, 8), [("A", 1)])
        self.assertIterEqual(self.store.diff(5, 5), [])
        self.assertIterEqual(self.store.diff(4, 4), [("A", 1)])
        self.assertIterEqual(self.store.diff(3, 3), [])
        self.assertIterEqual(self.store.diff(1, 1), [])

    def test_iter(self):
        """
        """

        self.store.add("A", "A1")
        self.store.add("B", "B1")
        self.store.add("C", "C1")

        self.assertIterEqual(self.store.iterate(), ["C1", "B1", "A1"])
        self.assertIterEqual(iter(self.store), ["C1", "B1", "A1"])

        self.store.commit()
        self.store.add("A", "A2")
        self.store.add("D", "D1")

        self.assertIterEqual(self.store.iterate(), ["D1", "C1", "B1", "A2"])
        self.assertIterEqual(iter(self.store), ["D1", "C1", "B1", "A2"])

    def test_nonzero(self):
        """
        Test coercion to boolean.
        """

        self.assertFalse(self.store)

        self.store.add("A", "A1")

        self.assertTrue(self.store)

        self.store.add("A", "A2")

        self.assertTrue(self.store)

        self.store.remove("A")

        self.assertFalse(self.store)
