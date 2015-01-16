========
SnapPass
========

.. image:: https://travis-ci.org/pinterest/snappass.png


It's like SnapChat... for Passwords.

This is a webapp that lets you share passwords securely.

Let's say you have a password.  You want to give it to your coworker, Jane.
You could email it to her, but then it's in her email, which might be backed up,
and probably is in some storage device controlled by the NSA.

You could send it to her over chat, but chances are Jane logs all her messages
because she uses Google Talk, and Google Talk logs everything.

You could write it down, but you can't find a pen, and there's way too many
characters because your Security Person, Paul, is paranoid.

So we build SnapPass.  It's not that complicated, it does one thing.  If
Jane gets a link to the password and never looks at it, the password goes away.
If the NSA gets a hold of the link, and they look at the password... well they
have the password.  Also, Jane can't get the password, but now Jane knows that
not only is someone looking in her email, they are clicking on links.

Anyway, this took us very little time to write, but we figure we'd save you the
trouble of writing it yourself, because maybe you are busy and have other things
to do.  Enjoy.

Requirements
------------

* Redis.
* Python 2.6, 2.7 or 3.3.

Installation
------------

::

    $ pip install snappass
    $ snappass
    * Running on http://0.0.0.0:5000/
    * Restarting with reloader

Configuration
-------------

You can configure the following via environment variables.

`REDIS_HOST` and `REDIS_PORT` tell SnapPass how to connect to your Redis Server. Defaults to localhost on port 6379.

`REDIS_DB` is the database that you want to use on that Redis server. Defaults to db 0.

`SECRET_KEY` this should be a unique key that's used to sign key.  This should
be kept secret.  See the `Flask Documentation`_ for more information.

.. _Flask Documentation: http://flask.pocoo.org/docs/quickstart/#sessions

`STATIC_URL` this should be the location of your static assets.  You might not
need to change this.

`NO_SSL` if you are not using SSL.
