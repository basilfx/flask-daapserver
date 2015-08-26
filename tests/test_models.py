# -*- coding: utf-8 -*-

from daapserver.models import Server, Database, Item, Container, ContainerItem

import unittest


class ModelsTest(unittest.TestCase):
    """
    Test models.
    """

    def test_unicode_str_repr(self):
        """
        Test model to unicode, string and representation methods.
        """

        server = Server(name=u"Björn Borg")
        db = Database(id=1, name=u"Hellö Wörld")
        item = Item(
            id=2, artist=u"Slagsmålsklubben", album="Fest i valen",
            name="Sponsored by Destiny")
        container = Container(id=3, name=u"Knäckebröd")
        container_item = ContainerItem(id=4, item_id=2, container_id=3)

        for instance in [server, db, item, container, container_item]:
            # Type checking
            self.assertTrue(type(unicode(instance)), unicode)
            self.assertTrue(type(str(instance)), str)
            self.assertTrue(type(repr(instance)), str)

            # String variant replaces non-ascii characters
            self.assertTrue(
                unicode(instance).encode("ascii", "replace") == str(instance))

    def test_store(self):
        """
        Test store references stay the same.
        """

        server = Server()

        database = Database(id=1, name="Database A")
        server.databases.add(database)

        item = Item(id=2, name="Item A")
        database.items.add(item)

        self.assertEqual(
            server.databases.store,
            server.databases(revision=1).store)
        self.assertEqual(
            server.databases[1].items.store,
            server.databases[1].items(revision=1).store)
        self.assertEqual(
            server.databases(revision=1)[1].items.store,
            server.databases[1].items(revision=1).store)

    def test_basis(self):
        """
        Test basic functionality.
        """

        server = Server()
        database = Database(id=1, name="Database A")
        server.databases.add(database)

        self.assertListEqual(server.databases.keys(), [1])

        database = Database(id=2, name="Database B")
        server.databases.add(database)

        self.assertListEqual(server.databases.keys(), [2, 1])

        server.commit(2)
        server.databases.remove(database)
        server.commit(3)

        self.assertListEqual(server.databases.keys(), [1])
        self.assertListEqual(server.databases(revision=2).keys(), [1])
        self.assertListEqual(server.databases(revision=1).keys(), [2, 1])

        with self.assertRaises(KeyError):
            server.databases[2]

        database = Database(id=3, name="Database C")

        server.databases.add(database)
        server.commit(4)

        self.assertListEqual(server.databases.keys(), [3, 1])
        self.assertListEqual(server.databases(revision=3).keys(), [3, 1])
        self.assertListEqual(server.databases(revision=2).keys(), [1])
        self.assertListEqual(server.databases(revision=1).keys(), [2, 1])

    def test_nested(self):
        """
        Test nesting of objects, with different revisions.
        """

        server = Server()

        server.commit(2)
        server.commit(3)
        server.commit(4)
        server.commit(5)
        server.commit(6)

        database = Database(id=1, name="Database A")

        server.databases.add(database)
        server.databases.remove(database)

        database = Database(id=2, name="Database B")

        item = Item(id=3, name="Item A")
        database.items.add(item)

        server.databases.add(database)
        database.items.add(item)

        self.assertListEqual(server.databases.keys(), [2])
        self.assertListEqual(server.databases(revision=6).keys(), [2])
        self.assertListEqual(server.databases(revision=5).keys(), [])
        self.assertListEqual(server.databases(revision=4).keys(), [])
        self.assertListEqual(server.databases(revision=3).keys(), [])
        self.assertListEqual(server.databases(revision=2).keys(), [])
        self.assertListEqual(server.databases(revision=1).keys(), [])

        with self.assertRaises(KeyError):
            server.databases[1]

        self.assertListEqual(server.databases[2].items.keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=1).keys(), [3])

        with self.assertRaises(ValueError):
            # Item was added to a database that was not in a server before
            # adding.
            self.assertListEqual(
                server.databases[2].items(revision=2).keys(), [3])

        server.commit(7)

        self.assertListEqual(server.databases[2].items.keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=7).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=6).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=5).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=4).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=3).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=2).keys(), [3])
        self.assertListEqual(server.databases[2].items(revision=1).keys(), [3])

    def test_diff(self):
        """
        Test diff of two sets, for updated and removed items.
        """

        server = Server()

        database = Database(id=1, name="Database A")
        server.databases.add(database)

        item = Item(id=2, name="Item A")
        database.items.add(item)

        server.commit(2)

        item = Item(id=2, name="Item A, version 2")
        database.items.add(item)

        items_1 = database.items(revision=1)
        items_2 = database.items(revision=2)

        self.assertListEqual(items_2.keys(), [2])
        self.assertListEqual(list(items_2.updated(items_1)), [2])

        server.commit(3)

        database.items.remove(item)

        server.commit(4)

        items_1 = database.items(revision=1)
        items_2 = database.items(revision=2)
        items_3 = database.items(revision=3)

        self.assertListEqual(items_1.keys(), [2])
        self.assertListEqual(items_2.keys(), [2])
        self.assertListEqual(items_3.keys(), [])
        self.assertListEqual(list(items_3.removed(items_1)), [2])
        self.assertListEqual(list(items_3.removed(items_2)), [2])
        self.assertListEqual(list(items_3.removed(items_3)), [])

    def test_commit(self):
        """
        Test for committing the server.
        """

        server = Server()

        self.assertEqual(server.databases.store.revision, 1)

        # Cannot commit to lower version than default (version 1).
        with self.assertRaises(ValueError):
            server.commit(0)

        server.commit(10)
        self.assertEqual(server.databases.store.revision, 10)

        # Cannot commit to lower version than last one (version 10).
        with self.assertRaises(ValueError):
            server.commit(9)

        server.commit(11)
        self.assertEqual(server.databases.store.revision, 11)

        # Add a database
        database = Database(id=1)
        server.databases.add(database)

        self.assertEqual(database.items.store.revision, 1)
        self.assertEqual(database.containers.store.revision, 1)

        # Commit will synchronize revision with children.
        server.commit(12)

        self.assertEqual(server.databases.store.revision, 12)
        self.assertEqual(database.items.store.revision, 12)
        self.assertEqual(database.containers.store.revision, 12)
