import os
import sys
import secrets
import typing

import redis
from flask import abort
from redis.exceptions import ConnectionError

# Initialize Redis
redis_client: redis.StrictRedis
if os.environ.get('MOCK_REDIS'):
    from fakeredis import FakeStrictRedis

    redis_client = FakeStrictRedis()  # type: ignore
elif os.environ.get('REDIS_URL'):
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        raise ValueError("REDIS_URL is empty")
    redis_client = redis.StrictRedis.from_url(redis_url)
else:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('SNAPPASS_REDIS_DB', 0))
    redis_client = redis.StrictRedis(
        host=redis_host, port=redis_port, db=redis_db)
REDIS_PREFIX: str = os.environ.get('REDIS_PREFIX', 'snappass')


def check_redis_alive(fn: typing.Callable) -> typing.Callable:
    def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        try:
            if fn.__name__ == 'main':
                redis_client.ping()
            return fn(*args, **kwargs)
        except ConnectionError as e:
            print(f'Failed to connect to redis! {e}')
            if fn.__name__ == 'main':
                sys.exit(0)
            else:
                return abort(500)

    return inner


@check_redis_alive
def set_password(password: str, ttl: int) -> str:
    """
    Store the encrypted password (payload) for the specified lifetime.

    Returns the storage key where the password is stored.
    """
    storage_key = f"{REDIS_PREFIX}{secrets.token_urlsafe(16)}"
    redis_client.set(storage_key, password, ex=ttl)
    return storage_key


@check_redis_alive
def get_password(storage_key: str) -> typing.Optional[str]:
    """
    From a given storage key, return the stored password payload.
    """
    password = redis_client.getdel(storage_key)

    if password is not None:
        if isinstance(password, str):
            return password
        return password.decode('utf-8')
    return None


@check_redis_alive
def password_exists(storage_key: str) -> bool:
    return bool(redis_client.exists(storage_key))
