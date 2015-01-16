import uuid

import unittest
from unittest import TestCase

from werkzeug.exceptions import ClientDisconnected

#noinspection PyPep8Naming
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

    def test_clean_input(self):
        # Test Bad Data
        with snappass.app.test_request_context(
                "/", data={'password': 'foo', 'ttl': 'bar'}, method='POST'):
            self.assertRaises(ClientDisconnected, snappass.clean_input)

        # No Password
        with snappass.app.test_request_context(
                "/", method='POST'):
            self.assertRaises(ClientDisconnected, snappass.clean_input)

        # No TTL
        with snappass.app.test_request_context(
                "/", data={'password': 'foo'}, method='POST'):
            self.assertRaises(ClientDisconnected, snappass.clean_input)

        with snappass.app.test_request_context(
                "/", data={'password': 'foo', 'ttl': 'hour'}, method='POST'):
            self.assertEqual((3600, 'foo'), snappass.clean_input())


class SnapPassRoutesTestCase(TestCase):
    #noinspection PyPep8Naming
    def setUp(self):
        snappass.app.config['TESTING'] = True
        self.app = snappass.app.test_client()

    def test_show_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.get('/{}'.format(key))
        self.assertEquals(200, rv.status_code)
        self.assertIn(password, rv.data)

    def test_get_unknown_key(self):
        key = uuid.uuid4().hex
        rv = self.app.get('/{}'.format(key))
        self.assertEquals(404, rv.status_code)

    def test_get_invalid_key(self):
        key = "not_a_hex_string"
        rv = self.app.get('/{}'.format(key))
        self.assertEquals(400, rv.status_code)

    def test_store_password(self):
        form = {'password': "I like novelty sharks!", 'ttl': "hour"}
        rv = self.app.post('/', data=form)
        self.assertEquals(200, rv.status_code)
        self.assertIn("Password stored", rv.data)

    def test_store_lengthy_password(self):
        password = "1234567890abcdefghijklmnopqrstuvwxyz" * 30000  # exceeds 1MB
        form = {'password': password, 'ttl': "hour"}
        rv = self.app.post('/', data=form)
        self.assertEquals(400, rv.status_code)


if __name__ == '__main__':
    unittest.main()

