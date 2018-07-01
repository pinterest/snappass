import os
import re
import sys
import uuid

import redis

from cryptography.fernet import Fernet
from flask import abort, Flask, jsonify, make_response, render_template, request
from redis.exceptions import ConnectionError
from werkzeug.urls import url_quote_plus
from werkzeug.urls import url_unquote_plus

SNEAKY_USER_AGENTS = ('Slackbot', 'facebookexternalhit', 'Twitterbot',
                      'Facebot', 'WhatsApp', 'SkypeUriPreview',
                      'Iframely')
SNEAKY_USER_AGENTS_RE = re.compile('|'.join(SNEAKY_USER_AGENTS))
NO_SSL = os.environ.get('NO_SSL', False)
TOKEN_SEPARATOR = '~'


app = Flask(__name__)
if os.environ.get('DEBUG'):
    app.debug = True
app.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))

if os.environ.get('MOCK_REDIS'):
    from mockredis import mock_strict_redis_client
    redis_client = mock_strict_redis_client()
elif os.environ.get('REDIS_URL'):
    redis_client = redis.StrictRedis.from_url(os.environ.get('REDIS_URL'))
else:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    redis_db = os.environ.get('SNAPPASS_REDIS_DB', 0)
    redis_client = redis.StrictRedis(
        host=redis_host, port=redis_port, db=redis_db)

TIME_CONVERSION = {'week': 604800, 'day': 86400, 'hour': 3600}


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


def encrypt(password):
    """
    Take a password string, encrypt it with Fernet symmetric encryption,
    and return the result (bytes), with the decryption key (bytes)
    """
    encryption_key = Fernet.generate_key()
    fernet = Fernet(encryption_key)
    encrypted_password = fernet.encrypt(password.encode('utf-8'))
    return encrypted_password, encryption_key


def decrypt(password, decryption_key):
    """
    Decrypt a password (bytes) using the provided key (bytes),
    and return the plain-text password (bytes).
    """
    fernet = Fernet(decryption_key)
    return fernet.decrypt(password)


def parse_token(token):
    token_fragments = token.split(TOKEN_SEPARATOR, 1)  # Split once, not more.
    storage_key = token_fragments[0]

    try:
        decryption_key = token_fragments[1].encode('utf-8')
    except IndexError:
        decryption_key = None

    return storage_key, decryption_key


@check_redis_alive
def set_password(password, ttl):
    """
    Encrypt and store the password for the specified lifetime.

    Returns a token comprised of the key where the encrypted password
    is stored, and the decryption key.
    """
    storage_key = uuid.uuid4().hex
    encrypted_password, encryption_key = encrypt(password)
    redis_client.setex(storage_key, ttl, encrypted_password)
    encryption_key = encryption_key.decode('utf-8')
    token = TOKEN_SEPARATOR.join([storage_key, encryption_key])
    return token


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


def empty(value):
    if not value:
        return True


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if empty(request.form.get('password', '')):
        abort(400)

    if empty(request.form.get('ttl', '')):
        abort(400)

    time_period = request.form['ttl'].lower()
    if time_period not in TIME_CONVERSION:
        abort(400)

    return TIME_CONVERSION[time_period], request.form['password']


def make_base_url():
    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")

    return base_url

def request_is_valid(request):
    """
    Ensure the request validates the following:
        - not made by some specific User-Agents (to avoid chat's preview feature issue)
    """
    return not SNEAKY_USER_AGENTS_RE.search(request.headers.get('User-Agent', ''))

def not_found_api():
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }

    return make_response(jsonify(message), 404)

def unsupported_media_type_api():
    message = {
            'status': 415,
            'message': 'Unsupported Media Type',
    }

    return make_response(jsonify(message), 415)

def bad_request_api():
    message = {
            'status': 400,
            'message': 'Bad Request',
    }

    return make_response(jsonify(message), 400)


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


@app.route('/api', methods=['GET'])
def index_api():
    base_url = make_base_url()

    return "Generate a password share link with the following command: \n\n" \
           'curl -X POST -H "Content-Type:application/json" -d \'{"password":"password-here","ttl":"week | day | hour"}\' ' + base_url + "api\n"


@app.route('/', methods=['POST'])
def handle_password():
    ttl, password = clean_input()
    token = set_password(password, ttl)

    base_url = make_base_url()

    link = base_url + url_quote_plus(token)
    return render_template('confirm.html', password_link=link)


@app.route('/api', methods=['POST'])
def handle_password_api():
    if not request.headers['Content-Type'] == 'application/json':
        return unsupported_media_type_api()

    payload = request.get_json()

    password = payload.get('password', None)

    if not password:
        return bad_request_api()

    time_period = payload.get('ttl', 'week').lower()

    if not time_period in TIME_CONVERSION:
        return bad_request_api()

    ttl = TIME_CONVERSION[time_period]

    key = set_password(password, ttl)

    base_url = make_base_url()

    link_web = base_url + url_quote_plus(key)
    link_api = base_url + "api/" + url_quote_plus(key)

    data = {
        'web' : link_web,
        'api' : link_api,
    }

    return jsonify(data)


@app.route('/<password_key>', methods=['GET'])
def show_password(password_key):
    if not request_is_valid(request):
        abort(404)
    password_key = url_unquote_plus(password_key)
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template('password.html', password=password)


@app.route('/api/<password_key>', methods=['GET'])
def get_password_api(password_key):
    password_key = url_unquote_plus(password_key)
    password = get_password(password_key)
    if not password:
        return not_found_api()

    base_url = make_base_url()

    data = {
        'password' : password
    }

    return jsonify(data)


@check_redis_alive
def main():
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
