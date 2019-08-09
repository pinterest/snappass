from mock import patch
import time
import unittest
import uuid
from unittest import TestCase

from cryptography.fernet import Fernet
from werkzeug.exceptions import BadRequest
from fakeredis import FakeStrictRedis

# noinspection PyPep8Naming
import snappass.main as snappass

__author__ = 'davedash'


class SnapPassTestCase(TestCase):

    @patch('redis.client.StrictRedis', FakeStrictRedis)
    def test_get_password(self):
        password = "melatonin overdose 1337!$"
        key = snappass.set_password(password, 30)
        self.assertEqual(password, snappass.get_password(key))
        # Assert that we can't look this up a second time.
        self.assertIsNone(snappass.get_password(key))

    def test_password_is_not_stored_in_plaintext(self):
        password = "trustno1"
        token = snappass.set_password(password, 30)
        redis_key = token.split(snappass.TOKEN_SEPARATOR)[0]
        stored_password_text = snappass.redis_client.get(redis_key).decode('utf-8')
        self.assertNotIn(password, stored_password_text)

    def test_returned_token_format(self):
        password = "trustsome1"
        token = snappass.set_password(password, 30)
        token_fragments = token.split(snappass.TOKEN_SEPARATOR)
        self.assertEqual(2, len(token_fragments))
        redis_key, encryption_key = token_fragments
        self.assertEqual(32 + len(snappass.REDIS_PREFIX), len(redis_key))
        try:
            Fernet(encryption_key.encode('utf-8'))
        except ValueError:
            self.fail('the encryption key is not valid')

    def test_encryption_key_is_returned(self):
        password = "trustany1"
        token = snappass.set_password(password, 30)
        token_fragments = token.split(snappass.TOKEN_SEPARATOR)
        redis_key, encryption_key = token_fragments
        stored_password = snappass.redis_client.get(redis_key)
        fernet = Fernet(encryption_key.encode('utf-8'))
        decrypted_password = fernet.decrypt(stored_password).decode('utf-8')
        self.assertEqual(password, decrypted_password)

    def test_unencrypted_passwords_still_work(self):
        unencrypted_password = "trustevery1"
        storage_key = uuid.uuid4().hex
        snappass.redis_client.setex(storage_key, 30, unencrypted_password)
        retrieved_password = snappass.get_password(storage_key)
        self.assertEqual(unencrypted_password, retrieved_password)

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
        self.assertIsNone(snappass.get_password(key))


class SnapPassRoutesTestCase(TestCase):
    # noinspection PyPep8Naming
    def setUp(self):
        snappass.app.config['TESTING'] = True
        self.app = snappass.app.test_client()

    def test_preview_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.get('/{0}'.format(key))
        self.assertNotIn(password, rv.get_data(as_text=True))

    def test_show_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.post('/{0}'.format(key))
        self.assertIn(password, rv.get_data(as_text=True))

    def test_url_prefix(self):
        password = "I like novelty kitten statues!"
        snappass.URL_PREFIX="/test/prefix"
        rv = self.app.post('/', data={'password': password, 'ttl': 'hour'})
        self.assertIn("localhost/test/prefix/", rv.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
