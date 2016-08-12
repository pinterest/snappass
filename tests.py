import unittest
from unittest import TestCase

from werkzeug.exceptions import BadRequest

# noinspection PyPep8Naming
import snappass.main as snappass

__author__ = 'davedash'


class SnapPassTestCase(TestCase):

    def test_set_password(self):
        """Ensure we return a 32-bit key."""
        key = snappass.set_password("foo", 30)
        self.assertEqual(32, len(key))

    def test_get_password(self):
        password = "melatonin overdose 1337!$"
        key = snappass.set_password(password, 30)
        self.assertEqual(password, snappass.get_password(key))
        # Assert that we can't look this up a second time.
        self.assertEqual(None, snappass.get_password(key))

    def test_password_is_decoded(self):
        password = "correct horse battery staple"
        key = snappass.set_password(password, 30)
        self.assertFalse(isinstance(snappass.get_password(key), bytes))

    def test_clean_input(self):
        # Test Bad Data
        with snappass.app.test_request_context(
                "/", data={'password': 'foo', 'ttl': 'bar'}, method='POST'):
            self.assertRaises(BadRequest, snappass.clean_input)

        # No Password
        with snappass.app.test_request_context(
                "/", method='POST'):
            self.assertRaises(BadRequest, snappass.clean_input)

        # No TTL
        with snappass.app.test_request_context(
                "/", data={'password': 'foo'}, method='POST'):
            self.assertRaises(BadRequest, snappass.clean_input)

        with snappass.app.test_request_context(
                "/", data={'password': 'foo', 'ttl': 'hour'}, method='POST'):
            self.assertEqual((3600, 'foo'), snappass.clean_input())


class SnapPassRoutesTestCase(TestCase):
    # noinspection PyPep8Naming
    def setUp(self):
        snappass.app.config['TESTING'] = True
        self.app = snappass.app.test_client()

    def test_show_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.get('/{0}'.format(key))
        self.assertTrue(password in rv.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
