import os
import re
import sys
import uuid
from flask import abort, Flask, render_template, request, jsonify

from werkzeug.urls import url_quote_plus
from werkzeug.urls import url_unquote_plus

from .encryption_utils import encrypt, decrypt, make_token, parse_token
from .redis_provider import redis_client, make_redis_storage_key

# Initialize Flask Application
app = Flask(__name__)

if os.environ.get('DEBUG'):
    app.debug = True
app.secret_key = os.environ.get('SECRET_KEY', uuid.uuid4().hex)
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))


TIME_CONVERSION = {'week': 604800, 'day': 86400, 'hour': 3600}


def apify(func):
    def wrapped(*args, **kwargs):
        is_api = request.args.get('api', default=0, type=int)
        template_name, result, *rest = func(*args, **kwargs)
        if is_api:
            return jsonify(result)
        else:
            return render_template(template_name, **result)
    # for flask function mapping we restore the name of the original function
    wrapped.__name__ = func.__name__
    return wrapped


def is_redis_alive():
    try:
        redis_client.ping()
        return True
    except:
        return False


def check_redis_alive(fn):
    def inner(*args, **kwargs):
        try:
            if fn.__name__ == 'main':
                redis_client.ping()
            return fn(*args, **kwargs)
        except ConnectionError as e:
            print('Failed to connect to redis! %s' % e.message)
            if fn.__name__ == 'main':
                sys.exit(0)
            else:
                return abort(500)
    return inner


@check_redis_alive
def set_password(password, ttl):
    """
    Encrypt and store the password for the specified lifetime.

    Returns a token comprised of the key where the encrypted password
    is stored, and the decryption key.
    """
    storage_key = make_redis_storage_key()
    encrypted_password, encryption_key = encrypt(password)
    redis_client.setex(storage_key, ttl, encrypted_password)
    return make_token(storage_key, encryption_key.decode('utf-8'))


@check_redis_alive
def get_password(token):
    """
    From a given token, return the initial password.

    If the token is tilde-separated, we decrypt the password fetched from Redis.
    If not, the password is simply returned as is.
    """
    storage_key, decryption_key = parse_token(token)
    password = redis_client.get(storage_key)
    redis_client.delete(storage_key)

    if password is not None:

        if decryption_key is not None:
            password = decrypt(password, decryption_key)

        return password.decode('utf-8')
    return None


@check_redis_alive
def password_exists(token):
    storage_key, _ = parse_token(token)
    return redis_client.exists(storage_key)


def empty(*values):
    return not all(values)


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if empty(request.form.get('password')):
        abort(400)

    time_period = request.form.get('ttl', '').lower()
    if time_period not in TIME_CONVERSION:
        abort(404)

    return TIME_CONVERSION[time_period], request.form['password']


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


@app.route('/', methods=['POST'])
@apify
def handle_password():
    ttl, password = clean_input()
    token = set_password(password, ttl)
    link = url_quote_plus(token)
    return 'confirm.html', dict(token=token)


@app.route('/<password_key>', methods=['GET'])
def preview_password(password_key):
    password_key = url_unquote_plus(password_key)
    if not password_exists(password_key):
        abort(404)
    return render_template('preview.html')


@app.route('/<password_key>', methods=['POST'])
@apify
def show_password(password_key):
    password_key = url_unquote_plus(password_key)
    password = get_password(password_key)
    if password is None:
        abort(404)

    return 'password.html', dict(password=password)


@check_redis_alive
def main():
    app.run(host='0.0.0.0')
