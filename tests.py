import time
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

    def test_password_before_expiration(self):
        password = 'fidelio'
        key = snappass.set_password(password, 1)
        self.assertEqual(password, snappass.get_password(key))

    def test_password_after_expiration(self):
        password = 'open sesame'
        key = snappass.set_password(password, 1)
        time.sleep(1.5)
        self.assertEqual(None, snappass.get_password(key))


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

    def test_bots_denial(self):
        """
        Main known bots User-Agent should be denied access
        """
        password = "Bots can't access this"
        key = snappass.set_password(password, 30)
        a_few_sneaky_bots = [
            "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
            "facebookexternalhit/1.1",
            "Facebot/1.0",
            "Twitterbot/1.0",
            "_WhatsApp/2.12.81 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00",
            "WhatsApp/2.16.6/i"
        ]

        for ua in a_few_sneaky_bots:
            rv = self.app.get('/{0}'.format(key), headers={ 'User-Agent': ua })
            self.assertEquals(rv.status_code, 404)


if __name__ == '__main__':
    unittest.main()
