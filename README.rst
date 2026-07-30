========
SnapPass
========

|pypi|

.. |pypi| image:: https://img.shields.io/pypi/v/snappass.svg
    :target: https://pypi.python.org/pypi/snappass
    :alt: Latest version released on PyPI

It's like SnapChat... for passwords.

This is a web app that lets you share passwords securely.

Let's say you have a password.  You want to give it to your coworker, Jane.
You could email it to her, but then it's in her email, which might be backed up,
and probably is in some storage device controlled by the NSA.

You could send it to her over chat, but chances are Jane logs all her messages
because she uses Google Hangouts Chat, and Google Hangouts Chat might log everything.

You could write it down, but you can't find a pen, and there's way too many
characters because your security person, Paul, is paranoid.

So we built SnapPass.  It's not that complicated, it does one thing.  If
Jane gets a link to the password and never looks at it, the password goes away.
If the NSA gets a hold of the link, and they look at the password... well they
have the password.  Also, Jane can't get the password, but now Jane knows that
not only is someone looking in her email, they are clicking on links.

Anyway, this took us very little time to write, but we figure we'd save you the
trouble of writing it yourself, because maybe you are busy and have other things
to do.  Enjoy.

Security
--------

Passwords are encrypted purely on the client-side using the Web Crypto API (AES-GCM).
The server only ever receives and stores the encrypted ciphertext and a random IV.
The encryption key is generated in the browser and transported via the URL hash fragment (``#key``) which is **never** sent to the server.
This means that even if someone has access to the Redis store or the application logs, the passwords remain completely safe.

Requirements
------------

* `Redis`_ 6.2.0 or newer
* Python 3.10+

.. _Redis: https://redis.io/

Installation
------------

::

    $ pip install snappass
    $ export SECRET_KEY="<your-secret-key-here>"
    $ snappass
    * Running on http://0.0.0.0:5000/
    * Restarting with reloader

Configuration
-------------

Start by ensuring that Redis is up and running.

Then, you can configure the following via environment variables.

``SECRET_KEY``: unique key that's used to sign key. This should
be kept secret.  See the `Flask Documentation`__ for more information.

.. __: http://flask.pocoo.org/docs/quickstart/#sessions

``DEBUG``: to run Flask web server in debug mode.  See the `Flask Documentation`__ for more information.

.. __: http://flask.pocoo.org/docs/quickstart/#debug-mode

``STATIC_URL``: this should be the location of your static assets.  You might not
need to change this.

``NO_SSL``: if you are not using SSL.

``URL_PREFIX``: useful when running snappass behind a reverse proxy like `nginx`. Example: ``"/some/path/"``, Defaults to ``None``

``REDIS_HOST``: this should be set by Redis, but you can override it if you want. Defaults to ``"localhost"``

``REDIS_PORT``: is the port redis is serving on, defaults to 6379

``SNAPPASS_REDIS_DB``: is the database that you want to use on this redis server. Defaults to db 0

``REDIS_URL``: (optional) will be used instead of ``REDIS_HOST``, ``REDIS_PORT``, and ``SNAPPASS_REDIS_DB`` to configure the Redis client object. For example: redis://username:password@localhost:6379/0

``REDIS_PREFIX``: (optional, defaults to ``"snappass"``) prefix used on redis keys to prevent collisions with other potential clients

``HOST_OVERRIDE``: (optional, recommended in production) Canonical hostname used to build the base URL for generated links. Useful when running behind reverse proxies like an identity-aware SSO, and prevents host header injection (see below). Example: ``sub.domain.com``

``SNAPPASS_BIND_ADDRESS``: (optional) Used to override the default bind address of 0.0.0.0 for flask app Example: ``127.0.0.1``

``SNAPPASS_PORT``: (optional) Used to override the default port of 5000 Example: ``6000``

Host Header Security
--------------------

SnapPass generates security-sensitive links (for password retrieval). When ``HOST_OVERRIDE`` is not set, the base URL of those links is derived from the request's ``Host`` header, which a client can spoof.

- Set ``HOST_OVERRIDE`` to your canonical hostname in production. It is then used for every generated link and the inbound ``Host`` header is ignored.
- If ``HOST_OVERRIDE`` is not set, SnapPass only derives the base URL from loopback hosts (``localhost``, ``127.0.0.1``, ``::1``); requests with any other ``Host`` header are rejected with ``400 Bad Request``.

APIs
----

SnapPass has 2 APIs :
1. A simple API : That can be used to create passwords links, and then share them with users
2. A more REST-y API : Which facilitate programmatic interactions with SnapPass, without having to parse HTML content when retrieving the password

Simple API
^^^^^^^^^^

The advantage of using the simple API is that you can create a password and retrieve the link without having to open the web interface. This is useful if you want to embed it in a script or use it in a CI/CD pipeline.

To create a password, send a POST request to ``/api/set_password`` like so. **Note:** The `password` field must be pre-encrypted and encoded in unpadded Base64URL.

::

    $ curl -X POST -H "Content-Type: application/json"  -d '{"password": "<base64url-encoded-iv-and-ciphertext>"}' http://localhost:5000/api/set_password/

This will return a JSON response with the password link:

::

    {
        "link": "http://127.0.0.1:5000/snappassd7x9aZ...",
        "ttl":1209600
    }

the default TTL is 2 weeks (1209600 seconds), but you can override it by adding a expiration parameter:

::

    $ curl -X POST -H "Content-Type: application/json"  -d '{"password": "<base64url-encoded-iv-and-ciphertext>", "ttl": 3600 }' http://localhost:5000/api/set_password/


REST API
^^^^^^^^

The advantage of using the REST API is that you can fully manage the lifecycle of the password stored in SnapPass without having to interact with any web user interface.

This is useful if you want to embed it in a script,  use it in a CI/CD pipeline or share it between multiple client applications.

Create a password
"""""""""""""""""

To create a password, send a POST request to ``/api/v2/passwords`` like so. **Note:** As with the simple API, the payload must be pre-encrypted:

::

    $ curl -X POST -H "Content-Type: application/json"  -d '{"password": "<base64url-encoded-iv-and-ciphertext>"}' http://localhost:5000/api/v2/passwords

This will return a JSON response with a token and the password link:

::

    {
        "token": "snappassd7x9aZ...",
        "links": [{
            "rel": "self",
            "href": "http://127.0.0.1:5000/api/v2/passwords/snappassd7x9aZ..."
        },{
            "rel": "web-view",
            "href": "http://127.0.0.1:5000/snappassd7x9aZ..."
        }],
        "ttl":1209600
    }

The default TTL is 2 weeks (1209600 seconds), but you can override it by adding a expiration parameter:

::

    $ curl -X POST -H "Content-Type: application/json"  -d '{"password": "<base64url-encoded-iv-and-ciphertext>", "ttl": 3600 }' http://localhost:5000/api/v2/passwords

If the password is null or empty, and the TTL is larger than the max TTL of the application, the API will return an error like this:


Otherwise, the API will return a 404 (Not Found) response like so:

::

    {
        "invalid-params": [{
            "name": "password",
            "reason": "The password is required and should not be null or empty."
        }, {
            "name": "ttl",
            "reason": "The specified TTL is longer than the maximum supported."
        }],
        "title": "The password and/or the TTL are invalid.",
        "type": "https://127.0.0.1:5000/set-password-validation-error"
    }

Check if a password exists
""""""""""""""""""""""""""

To check if a password exists, send a HEAD request to ``/api/v2/passwords/<token>``, where ``<token>`` is the token of the API response when a password is created (url encoded), or simply use the `self` link:

::

    $ curl --head http://localhost:5000/api/v2/passwords/snappassd7x9aZ...

If :
- the passwork_key is valid 
- the password :
  - exists,
  - has not been read 
  - is not expired

Then the API will return a 200 (OK) response like so:

::

    HTTP/1.1 200 OK
    Server: Werkzeug/3.0.1 Python/3.12.2
    Date: Fri, 29 Mar 2024 22:15:54 GMT
    Content-Type: text/html; charset=utf-8
    Content-Length: 0
    Connection: close

Otherwise, the API will return a 404 (Not Found) response like so:

::

    HTTP/1.1 404 NOT FOUND
    Server: Werkzeug/3.0.1 Python/3.12.2
    Date: Fri, 29 Mar 2024 22:19:29 GMT
    Content-Type: text/html; charset=utf-8
    Content-Length: 0
    Connection: close
    

Read a password
"""""""""""""""

To read a password, send a GET request to ``/api/v2/passwords/<password_key>``, where ``<password_key>`` is the token of the API response when a password is created, or simply use the `self` link:

::

    $ curl -X GET http://localhost:5000/api/v2/passwords/snappassd7x9aZ...

If :
- the token is valid 
- the password :
  - exists
  - has not been read 
  - is not expired

Then the API will return a 200 (OK) with a JSON response containing the password :

::

    {
        "password": "<base64url-encoded-iv-and-ciphertext>"
    }

Otherwise, the API will return a 404 (Not Found) response like so:

::

    {
        "invalid-params": [{
            "name": "token"
        }],
        "title": "The password doesn't exist.",
        "type": "https://127.0.0.1:5000/get-password-error"
    }

Notes on APIs
^^^^^^^^^^^^^

Notes:

- **Breaking Change in 1.7.0:** The backend no longer handles encryption. The ``password`` field sent to any API endpoint MUST be pre-encrypted by the client using AES-128-GCM. The payload must consist of a 12-byte IV concatenated with the ciphertext, and then encoded using unpadded Base64URL. The encryption key should never be sent to the server, and should instead be appended to the generated link as a URL hash fragment (``#``).
- When using the APIs, you can specify any ttl, as long as it is lower than the default.
- The password is passed in the body of the request rather than in the URL. This is to prevent the password from being logged in the server logs.
- Depending on the environment you are running it, you might want to expose the ``/api`` endpoint to your internal network only, and put the web interface behind authentication.


Docker
------

Alternatively, you can use `Docker`_ and `Docker Compose`_ to install and run SnapPass:

.. _Docker: https://www.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/

::

    $ docker-compose up -d

This will pull all dependencies, i.e. Redis and appropriate Python version (3.14), then start up SnapPass and Redis server. SnapPass server is accessible at: http://localhost:5000

Similar Tools
-------------

- `Snappass.NET <https://github.com/generateui/Snappass.NET>`_ is a .NET
  (ASP.NET Core) port of SnapPass.


We're Hiring!
-------------

Are you really excited about open-source and great software engineering?
`Pinterest is hiring <https://careers.pinterest.com>`_!
