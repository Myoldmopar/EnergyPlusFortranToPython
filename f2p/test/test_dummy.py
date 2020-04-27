from unittest import TestCase

from f2p.helpers import path_to_bin_ep_macro


class TestDummy(TestCase):

    def test_ep_macro_exists(self):
        ep_macro_path = path_to_bin_ep_macro()
        self.assertTrue(ep_macro_path.exists())

    def test_b(self):
        self.assertEqual(0, 0)

    def test_c(self):
        self.assertEqual(0, 0)

    def test_d(self):
        self.assertEqual(0, 0)
