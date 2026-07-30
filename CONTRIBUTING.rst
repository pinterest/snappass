============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/pinterest/snappass/issues.

If you are reporting a bug, please include:

* Your operating system name and version (if relevant).
* Any details about your local setup that might be helpful in troubleshooting.
* If you can, provide detailed steps to reproduce the bug.
* If you don't have steps to reproduce the bug, just note your observations in
  as much detail as you can. Questions to start a discussion about the issue
  are welcome.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
is open to whoever wants to implement it.


Write Documentation
~~~~~~~~~~~~~~~~~~~

Snappass could always use better documentation, whether as part of the
official docs, in docstrings, or even on the web in blog posts, articles, and
such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/pinterest/snappass/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Note that this project has an intentionally narrow scope.
  Our target users are small organizations that really need a
  quick and dirty way to exchange secrets.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)


Setting Up the Code for Local Development
-----------------------------------------

Here's how to set up ``snappass`` for local development.

1. Fork the ``snappass`` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/snappass.git

3. Install your local copy into a ``virtualenv``. It is recommended to use standard ``venv``::

    $ python -m venv venv
    $ source venv/bin/activate
    $ cd snappass/
    $ pip install -e .
    $ make dev

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. You run a development server with debug and autoreload to manually verify::

    $ docker run -d --name redis-server -p 6379:6379 redis
    $ make run

  You now have a running instance on localhost:5000/

6. Please add some tests to tests.py. When you're done making changes, check that your changes pass all tests and security linters (Ruff, Pip-Audit, etc.)::

    $ make test

   (Tox will automatically run all linting, security scans, and tests with coverage output.)

7. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

8. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work on all supported Python versions.

Releasing a New Version
-----------------------

This project uses `bumpversion <https://github.com/peritus/bumpversion>`_ to manage releases.
The `.bumpversion.cfg` file is configured to automatically update the version strings in both `pyproject.toml` and `snappass/__init__.py`, create a new git commit, and generate a git tag.

When you are ready to make a release, ensure you are on the main branch with a clean working directory, and run one of the following commands depending on the type of release (major, minor, or patch):

::

    $ bumpversion patch  # (e.g. 1.7.0 -> 1.7.1)
    $ bumpversion minor  # (e.g. 1.7.0 -> 1.8.0)
    $ bumpversion major  # (e.g. 1.7.0 -> 2.0.0)

Then, push the commit and the tags to GitHub:

::

    $ git push origin master --tags
