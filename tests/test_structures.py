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
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200), (3, 300)])
        self.assertListEqual(a.get_revision(1).added, [1, 2, 3])
        self.assertListEqual(a.get_revision(1).deleted, [])

        del a[1]
        del a[2]

        with self.assertRaises(KeyError):
            del a[2]

        with self.assertRaises(KeyError):
            del a[4]

        self.assertEqual(a.manager.revision, 2)
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200), (3, 300)])
        self.assertListEqual(a.get_revision(1).added, [1, 2, 3])
        self.assertListEqual(a.get_revision(1).deleted, [])
        self.assertListEqual(a.get_revision(2).items(), [(3, 300)])
        self.assertListEqual(a.get_revision(2).added, [3])
        self.assertListEqual(a.get_revision(2).deleted, [1, 2])

        a.commit()

        self.assertEqual(a.manager.revision, 2)
        self.assertDictEqual(a, {3: 300})

    def test_dict_abort_commit(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200

        self.assertEqual(a.manager.revision, 1)
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200)])
        self.assertListEqual(a.get_revision(1).added, [1, 2])
        self.assertListEqual(a.get_revision(1).deleted, [])

        a.abort()

        self.assertEqual(a.manager.revision, 0)
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [])
        self.assertListEqual(a.get_revision(1).added, [])
        self.assertListEqual(a.get_revision(1).deleted, [])

        a.commit()

        self.assertEqual(a.manager.revision, 0)
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [])
        self.assertListEqual(a.get_revision(1).added, [])
        self.assertListEqual(a.get_revision(1).deleted, [])

        a[1] = 100
        a[2] = 200

        self.assertEqual(a.manager.revision, 1)
        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200)])
        self.assertListEqual(a.get_revision(1).added, [1, 2])
        self.assertListEqual(a.get_revision(1).deleted, [])

        a.commit()

        self.assertEqual(a.manager.revision, 1)
        self.assertDictEqual(a, {1: 100, 2: 200})

    def test_dict_length(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200
        a[3] = 300

        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.get_revision(1)), 3)

        a.commit()

        self.assertEqual(len(a), 3)

        del a[2]

        self.assertEqual(len(a), 3)
        self.assertEqual(len(a.get_revision(2)), 2)

        a.commit()

        self.assertEqual(len(a), 2)

    def test_dict_length2(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200
        a[3] = 300

        self.assertEqual(len(a), 0)
        self.assertEqual(len(a.get_revision(1)), 3)
        self.assertEqual(a.manager.revision, 1)

        del a[1]

        self.assertEqual(len(a), 0)
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

        self.assertDictEqual(a, {})
        self.assertListEqual(a.get_revision(1).items(), [(1, b)])
        self.assertListEqual(a.get_revision(1).added, [1])
        self.assertListEqual(a.get_revision(1).deleted, [])
        self.assertDictEqual(b, {})
        self.assertListEqual(b.get_revision(1).items(), [(1, c)])
        self.assertListEqual(b.get_revision(1).added, [1])
        self.assertListEqual(b.get_revision(1).deleted, [])
        self.assertDictEqual(c, {})
        self.assertListEqual(c.get_revision(1).items(), [(1, 100)])
        self.assertListEqual(c.get_revision(1).added, [1])
        self.assertListEqual(c.get_revision(1).deleted, [])

        manager.commit()

        self.assertDictEqual(a, {1: b})
        self.assertDictEqual(b, {1: c})
        self.assertDictEqual(c, {1: 100})

        del b[1]

        self.assertEqual(manager.revision, 2)

        self.assertDictEqual(a, {1: b})
        self.assertListEqual(a.get_revision(2).items(), [(1, b)])
        self.assertListEqual(a.get_revision(2).added, [])
        self.assertListEqual(a.get_revision(2).deleted, [])
        self.assertDictEqual(b, {1: c})
        self.assertListEqual(b.get_revision(2).items(), [])
        self.assertListEqual(b.get_revision(2).added, [])
        self.assertListEqual(b.get_revision(2).deleted, [1])
        self.assertDictEqual(c, {1: 100})
        self.assertListEqual(c.get_revision(2).items(), [(1, 100)])
        self.assertListEqual(c.get_revision(2).added, [])
        self.assertListEqual(c.get_revision(2).deleted, [])

        manager.commit()

        self.assertDictEqual(a, {1: b})
        self.assertDictEqual(b, {})
        self.assertDictEqual(c, {1: 100})

    def test_dict_switch(self):
        a = RevisionDict()

        a[1] = 100
        a[2] = 200

        self.assertEqual(a.manager.revision, 1)

        self.assertListEqual(a.get_revision(1).items(), [(1, 100), (2, 200)])
        self.assertListEqual(a.get_revision(1).added, [1, 2])
        self.assertListEqual(a.get_revision(1).deleted, [])

        del a[1]

        self.assertEqual(a.manager.revision, 2)

        self.assertListEqual(a.get_revision(2).items(), [(2, 200)])
        self.assertListEqual(a.get_revision(2).added, [2])
        self.assertListEqual(a.get_revision(2).deleted, [1])

        a.manager = RevisionManager()

        self.assertEqual(a.manager.revision, 1)

        self.assertListEqual(a.get_revision(1).items(), [(2, 200)])
        self.assertListEqual(a.get_revision(1).added, [2])
        self.assertListEqual(a.get_revision(1).deleted, [])

        a.commit()

        self.assertDictEqual(a, {2: 200})