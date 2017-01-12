import os
import re
import sys
import uuid

import redis
from redis.exceptions import ConnectionError

from flask import abort, Flask, render_template, request, jsonify


SNEAKY_USER_AGENTS = ('Slackbot', 'facebookexternalhit', 'Twitterbot', 'Facebot', 'WhatsApp')
SNEAKY_USER_AGENTS_RE = re.compile('|'.join(SNEAKY_USER_AGENTS))
NO_SSL = os.environ.get('NO_SSL', False)
app = Flask(__name__)
if os.environ.get('DEBUG'):
   app.debug = True
app.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))

if os.environ.get('REDIS_URL'):
    redis_client = redis.StrictRedis.from_url(os.environ.get('REDIS_URL'))
else:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    redis_db = os.environ.get('SNAPPASS_REDIS_DB', 0)
    redis_client = redis.StrictRedis(
        host=redis_host, port=redis_port, db=redis_db)

time_conversion = {
    'week': 604800,
    'day': 86400,
    'hour': 3600
}


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
    key = uuid.uuid4().hex
    redis_client.setex(key, ttl, password)
    return key


@check_redis_alive
def get_password(key):
    password = redis_client.get(key)
    if password is not None:
        password = password.decode('utf-8')
    redis_client.delete(key)
    return password


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if 'password' not in request.form:
        abort(400)

    if 'ttl' not in request.form:
        abort(400)

    time_period = request.form['ttl'].lower()
    if time_period not in time_conversion:
        abort(400)

    return time_conversion[time_period], request.form['password']

def request_is_valid(request):
    """
    Ensure the request validates the following:
        - not made by some specific User-Agents (to avoid chat's preview feature issue)
    """
    return not SNEAKY_USER_AGENTS_RE.search(request.headers.get('User-Agent', ''))

def not_found_api(error=None):
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

def unsupported_media_type_api(error=None):
    message = {
            'status': 415,
            'message': 'Unsupported Media Type',
    }
    resp = jsonify(message)
    resp.status_code = 415

    return resp

def bad_request_api(error=None):
    message = {
            'status': 400,
            'message': 'Bad Request',
    }
    resp = jsonify(message)
    resp.status_code = 400

    return resp


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


@app.route('/api', methods=['GET'])
def index_api():
    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")

    return "Generate a password share link with the following command: \n\n" \
           "curl -X POST -d \'{\"password\":\"password-here\",\"ttl\":\"week | day | hour\"}\' -H \"Content-Type:application/json\" " + base_url + "api\n"


@app.route('/', methods=['POST'])
def handle_password():
    ttl, password = clean_input()
    key = set_password(password, ttl)

    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")
    link = base_url + key
    return render_template('confirm.html', password_link=link)


@app.route('/api', methods=['POST'])
def handle_password_api():
    if not request.headers['Content-Type'] == 'application/json':
        return unsupported_media_type_api()

    payload = request.get_json()

    if 'password' in payload:
        password = payload['password']

        if not len(password) > 0:
            return bad_request_api()
    else:
        return bad_request_api()

    if 'ttl' in payload:
        time_period = payload['ttl'].lower()
        if not time_period in time_conversion:
            return bad_request_api()

        ttl = time_conversion[time_period]
    else:
        # Set ttl to one week if not specified in the JSON
        ttl = 604800

    key = set_password(password, ttl)

    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")

    link_web = base_url + key
    link_api = base_url + "api/" + key

    data = {
        'web' : link_web,
        'api' : link_api,
    }

    resp = jsonify(data)
    resp.status_code = 200

    return resp


@app.route('/<password_key>', methods=['GET'])
def show_password(password_key):
    if not request_is_valid(request):
        abort(404)
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template('password.html', password=password)


@app.route('/api/<password_key>', methods=['GET'])
def get_password_api(password_key):
    password = get_password(password_key)
    if not password:
        return not_found_api()

    if NO_SSL:
        base_url = request.url_root
    else:
        base_url = request.url_root.replace("http://", "https://")

    data = {
        'password' : password
    }

    resp = jsonify(data)
    resp.status_code = 200

    return resp


@check_redis_alive
def main():
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
