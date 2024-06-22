import re
import time
import unittest
import uuid
from unittest import TestCase
from unittest import mock
from urllib.parse import quote
from urllib.parse import unquote

from cryptography.fernet import Fernet
from freezegun import freeze_time
from werkzeug.exceptions import BadRequest
from fakeredis import FakeStrictRedis

# noinspection PyPep8Naming
import snappass.main as snappass

__author__ = 'davedash'


class SnapPassTestCase(TestCase):

    @mock.patch('redis.client.StrictRedis', FakeStrictRedis)
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

    def test_health_check(self):
        response = self.app.get('/_/_/health')
        self.assertEqual('200 OK', response.status)
        self.assertEqual('{}', response.get_data(as_text=True).strip())

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
        snappass.URL_PREFIX = "/test/prefix"
        rv = self.app.post('/', data={'password': password, 'ttl': 'hour'})
        self.assertIn("localhost/test/prefix/", rv.get_data(as_text=True))

    def test_set_password(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post('/', data={'password': password, 'ttl': 'two weeks'})

            html_content = rv.data.decode("ascii")
            key = re.search(r'id="password-link" value="https://localhost/([^"]+)', html_content).group(1)
            key = unquote(key)

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_json(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/',
                headers={'Accept': 'application/json'},
                data={'password': password, 'ttl': 'two weeks'},
            )

            json_content = rv.get_json()
            key = re.search(r'https://localhost/([^"]+)', json_content['link']).group(1)
            key = unquote(key)

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_api(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/set_password/',
                headers={'Accept': 'application/json'},
                json={'password': password, 'ttl': '1209600'},
            )

            json_content = rv.get_json()
            key = re.search(r'https://localhost/([^"]+)', json_content['link']).group(1)
            key = unquote(key)

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_api_default_ttl(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/set_password/',
                headers={'Accept': 'application/json'},
                json={'password': password},
            )

            json_content = rv.get_json()
            key = re.search(r'https://localhost/([^"]+)', json_content['link']).group(1)
            key = unquote(key)

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_api_v2(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/v2/passwords',
                headers={'Accept': 'application/json'},
                json={'password': password, 'ttl': '1209600'},
            )

            json_content = rv.get_json()
            key = unquote(json_content['token'])

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_api_v2_default_ttl(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/v2/passwords',
                headers={'Accept': 'application/json'},
                json={'password': password},
            )

            json_content = rv.get_json()
            key = unquote(json_content['token'])

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_set_password_api_v2_no_password(self):
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': ''},
        )

        self.assertEqual(rv.status_code, 400)

        json_content = rv.get_json()
        invalid_params = json_content['invalid-params']
        self.assertEqual(len(invalid_params), 1)
        bad_password = invalid_params[0]
        self.assertEqual(bad_password['name'], 'password')

    def test_set_password_api_v2_too_big_ttl(self):
        password = 'my name is my passport. verify me.'
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': password, 'ttl': '1209600000'},
        )

        self.assertEqual(rv.status_code, 400)

        json_content = rv.get_json()
        invalid_params = json_content['invalid-params']
        self.assertEqual(len(invalid_params), 1)
        bad_ttl = invalid_params[0]
        self.assertEqual(bad_ttl['name'], 'ttl')

    def test_set_password_api_v2_no_password_and_too_big_ttl(self):
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': '', 'ttl': '1209600000'},
        )

        self.assertEqual(rv.status_code, 400)

        json_content = rv.get_json()
        invalid_params = json_content['invalid-params']
        self.assertEqual(len(invalid_params), 2)
        bad_password = invalid_params[0]
        self.assertEqual(bad_password['name'], 'password')
        bad_ttl = invalid_params[1]
        self.assertEqual(bad_ttl['name'], 'ttl')

    def test_check_password_api_v2(self):
        password = 'my name is my passport. verify me.'
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': password},
        )

        json_content = rv.get_json()
        key = unquote(json_content['token'])

        rvc = self.app.head('/api/v2/passwords/' + quote(key))
        self.assertEqual(rvc.status_code, 200)

    def test_check_password_api_v2_bad_keys(self):
        password = 'my name is my passport. verify me.'
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': password},
        )

        json_content = rv.get_json()
        key = unquote(json_content['token'])

        rvc = self.app.head('/api/v2/passwords/' + quote(key[::-1]))
        self.assertEqual(rvc.status_code, 404)

    def test_retrieve_password_api_v2(self):
        password = 'my name is my passport. verify me.'
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': password},
        )

        json_content = rv.get_json()
        key = unquote(json_content['token'])

        rvc = self.app.get('/api/v2/passwords/' + quote(key))
        self.assertEqual(rv.status_code, 200)

        json_content_retrieved = rvc.get_json()
        retrieved_password = json_content_retrieved['password']
        self.assertEqual(retrieved_password, password)

    def test_retrieve_password_api_v2_bad_keys(self):
        password = 'my name is my passport. verify me.'
        rv = self.app.post(
            '/api/v2/passwords',
            headers={'Accept': 'application/json'},
            json={'password': password},
        )

        json_content = rv.get_json()
        key = unquote(json_content['token'])

        rvc = self.app.get('/api/v2/passwords/' + quote(key[::-1]))
        self.assertEqual(rvc.status_code, 404)

        json_content_retrieved = rvc.get_json()
        invalid_params = json_content_retrieved['invalid-params']
        self.assertEqual(len(invalid_params), 1)
        bad_token = invalid_params[0]
        self.assertEqual(bad_token['name'], 'token')


if __name__ == '__main__':
    unittest.main()
