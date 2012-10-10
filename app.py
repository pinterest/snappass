import os
import uuid

import redis

from flask import abort, Flask, render_template, request


application = Flask(__name__)
application.secret_key = os.environ.get('SECRET_KEY', 'Secret Key')
application.config.update(dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))

id = lambda: uuid.uuid4().get_hex()
redis_host = os.environ.get('REDIS_HOST', 'localhost')
r = redis.StrictRedis(host=redis_host, port=6379, db=0)

time_conversion = {
    'week': 604800,
    'day': 86400,
    'hour': 3600
}

def set_password(password, ttl):
    key = id()
    r.set(key, password)
    r.expire(key, ttl)
    return key

def get_password(key):
    password = r.get(key)
    r.delete(key)
    return password

def clean_input():
    """
    Make sure we're not getting bad data from the front end,
    format data to be machine readable
    """
    if not 'password' in request.form:
        abort(400)

    if not 'ttl' in request.form:
        abort(400)

    time_period = request.form['ttl'].lower()
    if not time_period in time_conversion:
        abort(400)

    return time_conversion[time_period], request.form['password']
   
@application.route('/', methods=['GET'])
def index():
    return render_template('set_password.html')

@application.route('/', methods=['POST'])
def handle_password():
    ttl, password = clean_input()
    key = set_password(password, ttl)
    link = request.url_root.replace("http://", "https://") + key
    return render_template('confirm.html', password_link=link)

@application.route('/<password_key>', methods=['GET'])
def show_password(password_key):
    password = get_password(password_key)
    if not password:
        abort(404)

    return render_template('password.html', password=password)

if __name__ == '__main__':
    application.run(host='0.0.0.0', debug=True)
