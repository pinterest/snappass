Version 1.5.0 (in development)
------------------------------
* The ``URL_PREFIX`` environment variable can be used to add a prefix to URLs,
  which is useful when running behind a reverse proxy like nginx.
* Replaced mockredis with fakeredis in the unit test environment.

Version 1.4.2
-------------
 * Various minor README and documentation improvements
 * Upgrade to Jinja 2.10.1
 * Fix autocomplete bug where hitting "back" would allow to autocomplete the password

Version 1.4.1
-------------
 * Switch to local (non-CDN) Font Awesome assets
 * Upgraded cryptography to 2.3.1 (for CVE-2018-10903, although snappass is
   unaffected because it doesn't use the vulnerable ``finalize_with_tag`` API)

Version 1.4.0
-------------
*You will lose stored passwords during the upgrade to this version*
 * Added a prefix in redis in front of the storage keys, making the redis safer to share with other applications
 * Small test and syntax improvements

Version 1.3.0
-------------
* Quote urls to fix bug with ending in '='
* Mock redis
* Drop support for python 2.6 and python 3.3

Version 1.2.0
-------------
* Added Fernet cryptography to the stored keys, prevent access to full text passwords if someone has access to Redis
