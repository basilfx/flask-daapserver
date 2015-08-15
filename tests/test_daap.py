from daapserver.daap import DAAPObject, SpeedyDAAPObject

import cStringIO
import unittest


class DAAPTest(unittest.TestCase):
    """
    Test models.
    """

    def test_daap_object_encode(self):
        """
        Test encode DAAPObject.
        """

        daap_object = DAAPObject("dmap.status", 200)

        self.assertEqual(daap_object.code, "mstt")
        self.assertEqual(daap_object.value, 200)

        self.assertEqual(
            daap_object.encode(),
            "mstt\x00\x00\x00\x04\x00\x00\x00\xc8")

    def test_daap_object_decode(self):
        """
        Test decode DAAPObject.
        """

        daap_object = DAAPObject()

        daap_object.decode(
            cStringIO.StringIO("mstt\x00\x00\x00\x04\x00\x00\x00\xc8"))

        self.assertEqual(daap_object.code, "mstt")
        self.assertEqual(daap_object.value, 200)

    def test_speedy_daap_object_encode(self):
        """
        Test encode SpeedyDAAPObject.
        """

        speedy_daap_object = SpeedyDAAPObject("mstt", 5, 200)

        self.assertEqual(speedy_daap_object.code, "mstt")
        self.assertEqual(speedy_daap_object.value, 200)

        self.assertEqual(
            speedy_daap_object.encode(),
            "mstt\x00\x00\x00\x04\x00\x00\x00\xc8")
