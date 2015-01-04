from daapserver.models import Server, Database, Item

import unittest


class ModelsTest(unittest.TestCase):
    """
    Test models.
    """

    def test_basis(self):
        """
        Test basic functionality.
        """

        server = Server()

        database = Database()
        database.id = 1
        database.name = "Database A"
        server.databases.add(database)

        self.assertEqual(server.databases.keys(), [1])

        database = Database()
        database.id = 2
        database.name = "Database B"
        server.databases.add(database)

        self.assertEqual(server.databases.keys(), [1, 2])

        server.databases.remove(database)

        self.assertEqual(server.databases.keys(), [1])
        self.assertEqual(server.databases(revision=2).keys(), [1, 2])

        with self.assertRaises(KeyError):
            server.databases[2]

        database = Database()
        database.id = 3
        database.name = "Database C"
        server.databases.add(database)

        self.assertEqual(server.databases.keys(), [1, 3])
        self.assertEqual(server.databases(revision=4).keys(), [1, 3])

    def test_nested(self):
        """
        Test nesting of objects
        """

        server = Server()

        database = Database()
        database.id = 1
        database.name = "Database A"
        server.databases.add(database)
        server.databases.remove(database)

        database = Database()
        database.id = 2
        database.name = "Database B"

        item = Item()
        item.id = 3
        item.name = "Item A"

        with self.assertRaises(ValueError):
            database.items.add(item)

        server.databases.add(database)
        database.items.add(item)

        self.assertEqual(server.databases.keys(), [2])

    def test_invalid(self):
        """
        Test for adding item to removed database, then add it again.
        """

        server = Server()

        database = Database()
        database.id = 1
        database.name = "Database A"
        server.databases.add(database)
        server.databases.remove(database)

        item = Item()
        item.id = 2
        item.name = "Item A"

        with self.assertRaises(ValueError):
            database.items.add(item)

        server.databases.add(database)
        database.items.add(item)

    def test_invalid2(self):
        """
        Test for adding item to unassociated database.
        """

        database = Database()
        database.id = 1
        database.name = "Database A"

        item = Item()
        item.id = 2
        item.name = "Item A"

        with self.assertRaises(ValueError):
            database.items.add(item)

    def test_diff(self):
        """
        Test diff of two sets.
        """

        server = Server()

        database = Database()
        database.id = 1
        database.name = "Database A"
        server.databases.add(database)

        item = Item()
        item.id = 2
        item.name = "Item A"
        database.items.add(item)

        item = Item()
        item.id = 2
        item.name = "Item A, version 2"
        database.items.add(item)

        self.assertEqual(server.storage.revision, 3)

        items_1 = database.items(revision=2)
        items_2 = database.items(revision=3)

        self.assertEqual(items_2.edited(items_1), set([2]))
