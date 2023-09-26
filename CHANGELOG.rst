##########
Change Log
##########

******
Unreleased
******

Added
=====

* Shifting functionality into ``utils.py`` to simplify API module ``main.py``.
* Introducing ``CHANGELOG.rst`` for logging each version's changes.

Changed
=======

* Ignoring the __pycache__ folder in ``.gitignore``.

******
v0.1.0
******

Added
=====

* Created API with single post request at /search which performs a search amongst sources using analyzers and returns the results.
* Using Swagger documentation.