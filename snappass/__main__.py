import sys
import logging
import os
import sys
from gevent.pywsgi import WSGIServer

DEFAULT_PORT = 5000

def get_port():
    try:
        return int(sys.argv[1])
    except:
        logging.warning('defaulting to default port ', DEFAULT_PORT)
        return DEFAULT_PORT

if __name__ == "__main__" and (__package__ is None or __package__ == ''):
    __package__ = "snappass"
    sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))
    

    from .api import app

    logging.basicConfig(level=logging.INFO)
    port = get_port()
    

    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
