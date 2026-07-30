import os
import re
import time
import unittest
from unittest import TestCase
from urllib.parse import quote
from urllib.parse import unquote

from freezegun import freeze_time

os.environ['MOCK_REDIS'] = 'true'

# noinspection PyPep8Naming
import snappass.main as snappass  # noqa: E402
import snappass.storage as storage  # noqa: E402

__author__ = 'davedash'


class SnapPassTestCase(TestCase):

    def test_get_password(self):
        password = "melatonin overdose 1337!$"
        key = snappass.set_password(password, 30)
        self.assertEqual(password, snappass.get_password(key))
        # Assert that we can't look this up a second time.
        self.assertIsNone(snappass.get_password(key))

    def test_password_is_stored_exactly(self):
        # We now store exactly what the client sends
        # (which the client encrypts)
        password_payload = "encrypted_payload_base64"
        token = snappass.set_password(password_payload, 30)
        stored_password_text = storage.redis_client.get(token).decode('utf-8')
        self.assertEqual(password_payload, stored_password_text)

    def test_returned_token_format(self):
        password = "trustsome1"
        token = snappass.set_password(password, 30)
        # Should start with REDIS_PREFIX and be followed by
        # 22 chars of urlsafe base64
        self.assertTrue(token.startswith(storage.REDIS_PREFIX))
        # 16 bytes urlsafe base64 is 22 chars
        self.assertEqual(len(storage.REDIS_PREFIX) + 22, len(token))

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
        self.original_url_prefix = snappass.URL_PREFIX
        self.original_host_override = snappass.HOST_OVERRIDE

    def tearDown(self):
        # Restore module-level config mutated by tests so it does not leak
        # between test cases (URL_PREFIX by test_url_prefix, HOST_OVERRIDE by
        # test_uses_host_override_with_untrusted_host_header).
        snappass.URL_PREFIX = self.original_url_prefix
        snappass.HOST_OVERRIDE = self.original_host_override

    def test_health_check(self):
        response = self.app.get('/_/_/health')
        self.assertEqual('200 OK', response.status)
        self.assertEqual('{}', response.get_data(as_text=True).strip())

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_handle_password_invalid_ttl(self):
        rv = self.app.post('/', data={'password': 'foo', 'ttl': 'invalid'})
        self.assertEqual(rv.status_code, 400)

    def test_handle_password_missing_data(self):
        rv = self.app.post('/', data={})
        self.assertEqual(rv.status_code, 500)

    def test_preview_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.get('/{0}'.format(key))
        # The password payload should not be visible in preview
        self.assertNotIn(password, rv.get_data(as_text=True))

    def test_preview_password_not_found(self):
        rv = self.app.get('/invalid_key')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Secret Not Found', rv.get_data(as_text=True))

    def test_show_password(self):
        password = "I like novelty kitten statues!"
        key = snappass.set_password(password, 30)
        rv = self.app.post('/{0}'.format(key))
        # The payload (encrypted text) is shown in the text area
        self.assertIn(password, rv.get_data(as_text=True))

    def test_show_password_not_found(self):
        rv = self.app.post('/invalid_key')
        self.assertEqual(rv.status_code, 404)
        self.assertIn('Secret Not Found', rv.get_data(as_text=True))

    def test_url_prefix(self):
        password = "I like novelty kitten statues!"
        snappass.URL_PREFIX = "/test/prefix"
        rv = self.app.post('/', data={'password': password, 'ttl': 'hour'})
        self.assertIn("localhost/test/prefix/", rv.get_data(as_text=True))

    def test_set_password_json(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/',
                headers={'Accept': 'application/json'},
                data={'password': password, 'ttl': 'two weeks'},
            )

            json_content = rv.get_json()
            match = re.search(r'https://localhost/([^"]+)',
                              json_content['link'])
            key = unquote(match.group(1))

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
                json={'password': password, 'ttl': 1209600},
            )

            json_content = rv.get_json()
            match = re.search(r'https://localhost/([^"]+)',
                              json_content['link'])
            key = unquote(match.group(1))

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_api_handle_password_missing_data(self):
        rv = self.app.post(
            '/api/set_password/',
            headers={'Accept': 'application/json'},
            json={}
        )
        self.assertEqual(rv.status_code, 500)

    def test_set_password_api_default_ttl(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/set_password/',
                headers={'Accept': 'application/json'},
                json={'password': password},
            )

            json_content = rv.get_json()
            match = re.search(r'https://localhost/([^"]+)',
                              json_content['link'])
            key = unquote(match.group(1))

            frozen_time.move_to("2020-05-22 11:59:59")
            self.assertEqual(snappass.get_password(key), password)

            frozen_time.move_to("2020-05-22 12:00:00")
            self.assertIsNone(snappass.get_password(key))

    def test_rejects_untrusted_host_header(self):
        rv = self.app.post(
            '/api/set_password/',
            headers={'Host': 'evil.com', 'Accept': 'application/json'},
            json={'password': 'my secret', 'ttl': 1209600},
        )

        self.assertEqual(rv.status_code, 400)

    def test_rejects_empty_host_header(self):
        rv = self.app.post(
            '/api/set_password/',
            headers={'Host': '', 'Accept': 'application/json'},
            json={'password': 'my secret', 'ttl': 1209600},
        )

        self.assertEqual(rv.status_code, 400)

    def test_uses_host_override_with_untrusted_host_header(self):
        snappass.HOST_OVERRIDE = 'snappass.example.org'
        rv = self.app.post(
            '/api/set_password/',
            headers={'Host': 'evil.com', 'Accept': 'application/json'},
            json={'password': 'my secret', 'ttl': 1209600},
        )

        self.assertEqual(rv.status_code, 200)
        json_content = rv.get_json()
        self.assertTrue(
            json_content['link'].startswith('https://snappass.example.org/')
        )

    def test_set_password_api_v2(self):
        with freeze_time("2020-05-08 12:00:00") as frozen_time:
            password = 'my name is my passport. verify me.'
            rv = self.app.post(
                '/api/v2/passwords',
                headers={'Accept': 'application/json'},
                json={'password': password, 'ttl': 1209600},
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
            json={'password': password, 'ttl': 1209600000},
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
            json={'password': '', 'ttl': 1209600000},
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
