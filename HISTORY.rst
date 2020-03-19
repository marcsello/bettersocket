=======
History
=======

0.1.1 (2020-03-19)
------------------

* Removed the exposed fileio, as it were confusing (see. https://github.com/marcsello/bettersocket/issues/1)
* Fixed `__str__` and `__repr__` functions on `BetterSocketIO` class to support other address families than INET
* Exposed `reset` call in `BetterSocketIO` class
* Various cleanups, and bugfixes
* Removed support for Python 3.5

0.1.0 (2020-02-20)
------------------

* First release on PyPI.
