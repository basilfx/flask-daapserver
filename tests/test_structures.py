from daapserver.structures import RevisionManager, RevisionDict

import unittest
import random

class RevisionTest(unittest.TestCase):

    def test_dict_simple(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200
        a[3] = 300

        self.assertEqual(a.manager.revision, 1)
        self.assertListEqual(a.items(), [(1, 100), (2, 200), (3, 300)])
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200), (3, 300)])

        del a[1]
        del a[2]

        with self.assertRaises(KeyError):
            del a[2]

        with self.assertRaises(KeyError):
            del a[4]

        self.assertEqual(a.manager.revision, 2)
        self.assertListEqual(a.items(), [(3, 300)])
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200), (3, 300)])
        self.assertListEqual(a.get_revision(2).items(), [(3, 300)])

        a.commit()

        self.assertEqual(a.manager.revision, 2)
        self.assertListEqual(a.items(), [(3, 300)])

    def test_dict_length(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200
        a[3] = 300

        self.assertEqual(len(a), 3)
        self.assertEqual(len(a.get_revision(1)), 3)
        self.assertEqual(a.manager.revision, 1)

        a.commit()

        self.assertEqual(len(a), 3)
        self.assertEqual(len(a.get_revision(1)), 3)
        self.assertEqual(a.manager.revision, 1)

        del a[2]

        self.assertEqual(len(a), 2)
        self.assertEqual(len(a.get_revision(2)), 2)
        self.assertEqual(a.manager.revision, 2)

        a.commit()

        self.assertEqual(len(a), 2)

    def test_dict_length2(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200
        a[3] = 300

        self.assertEqual(len(a), 3)
        self.assertEqual(len(a.get_revision(1)), 3)
        self.assertEqual(a.manager.revision, 1)

        del a[1]

        self.assertEqual(len(a), 2)
        self.assertEqual(len(a.get_revision(2)), 2)
        self.assertEqual(a.manager.revision, 2)

    def test_dict_nested(self):
        manager = RevisionManager()

        a = RevisionDict(manager)
        b = RevisionDict(manager)
        c = RevisionDict(manager)

        self.assertEqual(a.manager, manager)
        self.assertEqual(b.manager, manager)
        self.assertEqual(c.manager, manager)

        self.assertEqual(manager.revision, 0)

        a[1] = b
        b[1] = c
        c[1] = 100

        self.assertEqual(manager.revision, 1)

        self.assertListEqual(a.items(), [(1, b)])
        self.assertListEqual(a.get_revision(1).items(), [(1, b)])
        self.assertListEqual(b.items(), [(1, c)])
        self.assertListEqual(b.get_revision(1).items(), [(1, c)])
        self.assertListEqual(c.items(), [(1, 100)])
        self.assertListEqual(c.get_revision(1).items(), [(1, 100)])

        manager.commit()

        self.assertListEqual(a.items(), [(1, b)])
        self.assertListEqual(b.items(), [(1, c)])
        self.assertListEqual(c.items(), [(1, 100)])

        del b[1]

        self.assertEqual(manager.revision, 2)

        self.assertListEqual(a.items(), [(1, b)])
        self.assertListEqual(a.get_revision(2).items(), [(1, b)])
        self.assertListEqual(b.items(), [])
        self.assertListEqual(b.get_revision(2).items(), [])
        self.assertListEqual(c.items(), [(1, 100)])
        self.assertListEqual(c.get_revision(2).items(), [(1, 100)])

        manager.commit()

        self.assertListEqual(a.items(), [(1, b)])
        self.assertListEqual(b.items(), [])
        self.assertListEqual(c.items(), [(1, 100)])

    def test_dict_switch(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200

        self.assertEqual(a.manager.revision, 1)
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200)])

        del a[1]

        self.assertEqual(a.manager.revision, 2)
        self.assertListEqual(a.get_revision(2).items(), [(2, 200)])

        a.manager = RevisionManager()

        self.assertEqual(a.manager.revision, 1)
        self.assertListEqual(a.get_revision(1).items(), [(2, 200)])

        a.commit()

        self.assertListEqual(a.items(), [(2, 200)])