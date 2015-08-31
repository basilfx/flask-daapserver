from daapserver.provider import Provider
from daapserver.models import Server

import unittest


class Latch(object):
    """
    Provide a way to test if hooks were fired.
    """

    def __init__(self):
        """
        Construct a new latch.
        """

        self.toggled = False
        self.args = None
        self.kwargs = None

    def __call__(self, *args, **kwargs):
        """
        Toggle the latch when invoked
        """

        self.toggled = True
        self.args = args
        self.kwargs = kwargs


class TestProvider(unittest.TestCase):

    def setUp(self):
        """
        Initialize an empty provider.
        """

        self.provider = Provider()
        self.provider.server = Server()

    def test_hooks(self):
        """
        Test hooks for provider events.
        """

        updated = Latch()
        session_created = Latch()
        session_destroyed = Latch()

        self.provider.hooks["updated"].append(updated)
        self.provider.hooks["session_created"].append(session_created)
        self.provider.hooks["session_destroyed"].append(session_destroyed)

        self.provider.update()
        self.assertTrue(updated.toggled)

        self.provider.create_session("User-Agent", "127.0.0.1", "1.0")
        self.assertTrue(session_created.toggled)
        self.assertEqual(session_created.args[0], 1)

        self.provider.destroy_session(1)
        self.assertTrue(session_destroyed.toggled)
        self.assertEqual(session_destroyed.args[0], 1)
