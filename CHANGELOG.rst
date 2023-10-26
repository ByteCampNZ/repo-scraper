##########
Change Log
##########

******
v0.1.2
******

Changed
=======

* Restructuring project into a package.
* Introducing parameter ``db_path`` to script
* Changing ``README.rst`` to remove TODO-style phrasing.
* Removed version from ``swagger_config.json`` as it is already set dynamically by ``main.py``.
* Moved the ``requirements.txt`` out of the application folder and into the project folder.
* Obtaining API version from the package version.

******
v0.1.1
******

Added
=====

* Shifting functionality into ``utils.py`` to simplify API module ``main.py``.
* Introducing ``CHANGELOG.rst`` for logging each version's changes.

Changed
=======

* Ignoring the __pycache__ folder in ``.gitignore``.
* Improving the README to be more specific.
* Upgrading required packages ``codesurvey`` and ``flask``.

******
v0.1.0
******

Added
=====

* Created API with single post request at /search which performs a search amongst sources using analyzers and returns the results.
* Using Swagger documentation.
