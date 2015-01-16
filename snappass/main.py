import os
import re
import uuid

import redis

from flask import abort, Flask, render_template, request


MAX_PASSWORD_SIZE = 1048576
NO_SSL = os.environ.get('NO_SSL', False)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))

id_ = lambda: uuid.uuid4().hex
key_regexp = re.compile("^[0-9a-f]{32}$")
redis_safe_key = lambda key: "snappass:" + str(key)
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_client = redis.StrictRedis(host=redis_host, port=6379, db=0)

time_conversion = {
    'week': 604800,
    'day': 86400,
    'hour': 3600
}


def set_password(password, ttl):
    key = id_()
    redis_client.set(redis_safe_key(key), password)
    redis_client.expire(redis_safe_key(key), ttl)
    return key


def get_password(key):
    password = redis_client.get(redis_safe_key(key))
    redis_client.delete(redis_safe_key(key))
    return password


def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if not 'password' in request.form:
        abort(400)

    if len(request.form['password']) > MAX_PASSWORD_SIZE:
        abort(400)

    if not 'ttl' in request.form:
        abort(400)

    time_period = request.form['ttl'].lower()
    if not time_period in time_conversion:
        abort(400)

    return time_conversion[time_period], request.form['password']


@app.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')


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


@app.route('/<password_key>', methods=['GET'])
def show_password(password_key):
    if not key_regexp.match(password_key):
        abort(400)
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template('password.html', password=password)


def main():
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
