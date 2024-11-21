import os
import sys
import uuid

import redis

from cryptography.fernet import Fernet
from flask import abort, Flask, render_template, request, jsonify, make_response
from redis.exceptions import ConnectionError
from urllib.parse import quote_plus
from urllib.parse import unquote_plus
from urllib.parse import urljoin
from distutils.util import strtobool
# _ is required to get the Jinja templates translated
from flask_babel import Babel, _  # noqa: F401

NO_SSL = bool(strtobool(os.environ.get('NO_SSL', 'False')))
URL_PREFIX = os.environ.get('URL_PREFIX', None)
HOST_OVERRIDE = os.environ.get('HOST_OVERRIDE', None)
TOKEN_SEPARATOR = '~'

# Initialize Flask Application
app = Flask(__name__)
if os.environ.get('DEBUG'):
    app.debug = True
app.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))


# Set up Babel
def get_locale():
    return request.accept_languages.best_match(['en', 'es', 'de', 'nl', 'fr'])


babel = Babel(app, locale_selector=get_locale)

# Initialize Redis
if os.environ.get('MOCK_REDIS'):
    from fakeredis import FakeStrictRedis

    redis_client = FakeStrictRedis()
elif os.environ.get('REDIS_URL'):
    redis_client = redis.StrictRedis.from_url(os.environ.get('REDIS_URL'))
else:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    redis_db = os.environ.get('SNAPPASS_REDIS_DB', 0)
    redis_client = redis.StrictRedis(
        host=redis_host, port=redis_port, db=redis_db)
REDIS_PREFIX = os.environ.get('REDIS_PREFIX', 'snappass')

TIME_CONVERSION = {'two weeks': 1209600, 'week': 604800, 'day': 86400,
                   'hour': 3600}
DEFAULT_API_TTL = 1209600
MAX_TTL = DEFAULT_API_TTL


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


def as_validation_problem(request, problem_type, problem_title, invalid_params):
    base_url = set_base_url(request)

    problem = {
        "type": base_url + problem_type,
        "title": problem_title,
        "invalid-params": invalid_params
    }
    return as_problem_response(problem)


def as_not_found_problem(request, problem_type, problem_title, invalid_params):
    base_url = set_base_url(request)

    problem = {
        "type": base_url + problem_type,
        "title": problem_title,
        "invalid-params": invalid_params
    }
    return as_problem_response(problem, 404)


def as_problem_response(problem, status_code=None):
    if not isinstance(status_code, int) or not status_code:
        status_code = 400

    response = make_response(jsonify(problem), status_code)
    response.headers['Content-Type'] = 'application/problem+json'
    return response


@check_redis_alive
def set_password(password, ttl):
    """
    Encrypt and store the password for the specified lifetime.

    Returns a token comprised of the key where the encrypted password
    is stored, and the decryption key.
    """
    storage_key = REDIS_PREFIX + uuid.uuid4().hex
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


@check_redis_alive
def password_exists(token):
    storage_key, decryption_key = parse_token(token)
    return redis_client.exists(storage_key)


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


def set_base_url(req):
    if NO_SSL:
        if HOST_OVERRIDE:
            base_url = f'http://{HOST_OVERRIDE}/'
        else:
            base_url = req.url_root
    else:
        if HOST_OVERRIDE:
            base_url = f'https://{HOST_OVERRIDE}/'
        else:
            base_url = req.url_root.replace("http://", "https://")
    if URL_PREFIX:
        base_url = base_url + URL_PREFIX.strip("/") + "/"
    return base_url


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


@app.route('/', methods=['POST'])
def handle_password():
    password = request.form.get('password')
    ttl = request.form.get('ttl')
    if clean_input():
        ttl = TIME_CONVERSION[ttl.lower()]
        token = set_password(password, ttl)
        base_url = set_base_url(request)
        link = base_url + quote_plus(token)
        if request.accept_mimetypes.accept_json and not \
           request.accept_mimetypes.accept_html:
            return jsonify(link=link, ttl=ttl)
        else:
            return render_template('confirm.html', password_link=link)
    else:
        abort(500)


@app.route('/api/set_password/', methods=['POST'])
def api_handle_password():
    password = request.json.get('password')
    ttl = int(request.json.get('ttl', DEFAULT_API_TTL))
    if password and isinstance(ttl, int) and ttl <= MAX_TTL:
        token = set_password(password, ttl)
        base_url = set_base_url(request)
        link = base_url + quote_plus(token)
        return jsonify(link=link, ttl=ttl)
    else:
        abort(500)


@app.route('/api/v2/passwords', methods=['POST'])
def api_v2_set_password():
    password = request.json.get('password')
    ttl = int(request.json.get('ttl', DEFAULT_API_TTL))

    invalid_params = []

    if not password:
        invalid_params.append({
            "name": "password",
            "reason": "The password is required and should not be null or empty."
        })

    if not isinstance(ttl, int) or ttl > MAX_TTL:
        invalid_params.append({
            "name": "ttl",
            "reason": "The specified TTL is longer than the maximum supported."
        })

    if len(invalid_params) > 0:
        # Return a ProblemDetails expliciting issue with Password and/or TTL
        return as_validation_problem(
            request,
            "set-password-validation-error",
            "The password and/or the TTL are invalid.",
            invalid_params
        )

    token = set_password(password, ttl)
    url_token = quote_plus(token)
    base_url = set_base_url(request)
    api_link = urljoin(base_url, request.path + "/" + url_token)
    web_link = urljoin(base_url, url_token)
    response_content = {
        "token": token,
        "links": [{
            "rel": "self",
            "href": api_link
        }, {
            "rel": "web-view",
            "href": web_link
        }],
        "ttl": ttl
    }
    return jsonify(response_content)


@app.route('/api/v2/passwords/<token>', methods=['HEAD'])
def api_v2_check_password(token):
    token = unquote_plus(token)
    if not password_exists(token):
        # Return NotFound, to indicate that password does not exists (anymore or at all)
        return ('', 404)
    else:
        # Return OK, to indicate that password still exists
        return ('', 200)


@app.route('/api/v2/passwords/<token>', methods=['GET'])
def api_v2_retrieve_password(token):
    token = unquote_plus(token)
    password = get_password(token)
    if not password:
        # Return NotFound, to indicate that password does not exists (anymore or at all)
        return as_not_found_problem(
            request,
            "get-password-error",
            "The password doesn't exist.",
            [{"name": "token"}]
        )
    else:
        # Return OK and the password in JSON message
        return jsonify(password=password)


@app.route('/<password_key>', methods=['GET'])
def preview_password(password_key):
    password_key = unquote_plus(password_key)
    if not password_exists(password_key):
        return render_template('expired.html'), 404

    return render_template('preview.html')


@app.route('/<password_key>', methods=['POST'])
def show_password(password_key):
    password_key = unquote_plus(password_key)
    password = get_password(password_key)
    if not password:
        return render_template('expired.html'), 404

    return render_template('password.html', password=password)


@app.route('/_/_/health', methods=['GET'])
@check_redis_alive
def health_check():
    return {}


@check_redis_alive
def main():
    app.run(host=os.environ.get('SNAPPASS_BIND_ADDRESS', '0.0.0.0'),
            port=os.environ.get('SNAPPASS_PORT', 5000))


if __name__ == '__main__':
    main()
