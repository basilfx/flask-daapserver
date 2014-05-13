from daapserver.provider import Server, Database, Container, Item

import unittest

class ProviderTest(unittest.TestCase):

    def test_structure(self):
        server = Server()
        item = Item(id=3)
        container = Container(id=2)
        database = Database(id=1)

        database.add_item(item)
        container.add_item(item)
        database.add_container(container)
        server.add_database(database)

        self.assertEqual(server.manager, container.manager)
        self.assertEqual(server.manager, database.manager)
        self.assertEqual(database.manager, container.manager)

        self.assertEqual(server.databases.manager, server.manager)
        self.assertEqual(container.items.manager, container.manager)
        self.assertEqual(database.containers.manager, database.manager)
        self.assertEqual(database.items.manager, database.manager)

        self.assertEqual(server.manager.revision, 1)

        item_two = Item(id=4)

        with self.assertRaises(ValueError):
            container.add_item(item_two)

        database.add_item(item_two)
        container.add_item(item_two)

        self.assertEqual(server.manager.revision, 1)

        container.delete_item(item_two)

        self.assertEqual(server.manager.revision, 2)

        database.delete_container(container)

        self.assertEqual(server.manager.revision, 3)

        container.delete_item(item)

        self.assertNotEqual(server.manager, container.manager)
        self.assertEqual(server.manager.revision, 3)

        server.delete_database(database)

        self.assertNotEqual(server.manager, database.manager)
        self.assertNotEqual(container.manager, database.manager)
        self.assertEqual(server.manager.revision, 4)

        container.add_item(item)

        self.assertNotEqual(container.manager, database.manager)
        self.assertEqual(server.manager.revision, 4)

        database.add_container(container)

        self.assertEqual(container.manager, database.manager)
        self.assertEqual(server.manager.revision, 4)

    def test_structures_revision(self):

        server = Server()
        database = Database(id=1)
        container = Container(id=2)
        item_one = Item(id=3)
        item_two = Item(id=4)
        item_three = Item(id=5)

        server.add_database(database)
        database.add_container(container)
        database.add_item(item_one)
        database.add_item(item_two)
        database.add_item(item_three)

        self.assertEqual(server.manager.revision, 1)

        database.delete_item(item_three)

        self.assertEqual(server.manager.revision, 2)

        database.add_item(item_three)
        container.add_item(item_three)

        self.assertEqual(server.manager.revision, 3)

        view = server.get_revision(1)

        self.assertListEqual(view.databases[1].items.items(), [(3, item_one), (4, item_two), (5, item_three)])
        self.assertTrue(item_three not in view.databases[1].containers[2].items.values())
        self.assertEqual(len(view.databases[1].items), 3)

        view = server.get_revision(2)

        self.assertListEqual(view.databases[1].items.items(), [(3, item_one), (4, item_two)])
        self.assertTrue(item_three not in view.databases[1].containers[2].items.values())
        self.assertEqual(len(view.databases[1].items), 2)

        view = server.get_revision(3)

        self.assertListEqual(view.databases[1].items.items(), [(3, item_one), (4, item_two), (5, item_three)])
        self.assertTrue(item_three in view.databases[1].containers[2].items.values())
        self.assertEqual(len(view.databases[1].items), 3)