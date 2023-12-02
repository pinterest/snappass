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

Passwords are encrypted using `Fernet`_ symmetric encryption, from the `cryptography`_ library.
A random unique key is generated for each password, and is never stored;
it is rather sent as part of the password link.
This means that even if someone has access to the Redis store, the passwords are still safe.

.. _Fernet: https://cryptography.io/en/latest/fernet/
.. _cryptography: https://cryptography.io/en/latest/

Requirements
------------

* `Redis`_
* Python 3.8+

.. _Redis: https://redis.io/

Installation
------------

::

    $ pip install snappass
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

``HOST_OVERRIDE``: (optional) Used to override the base URL if the app is unaware. Useful when running behind reverse proxies like an identity-aware SSO. Example: ``sub.domain.com``

Docker
------

Alternatively, you can use `Docker`_ and `Docker Compose`_ to install and run SnapPass:

.. _Docker: https://www.docker.com/
.. _Docker Compose: https://docs.docker.com/compose/

::

    $ docker-compose up -d

This will pull all dependencies, i.e. Redis and appropriate Python version (3.7), then start up SnapPass and Redis server. SnapPass server is accessible at: http://localhost:5000

Similar Tools
-------------

- `Snappass.NET <https://github.com/generateui/Snappass.NET>`_ is a .NET
  (ASP.NET Core) port of SnapPass.


We're Hiring!
-------------

Are you really excited about open-source and great software engineering?
`Pinterest is hiring <https://careers.pinterest.com>`_!
