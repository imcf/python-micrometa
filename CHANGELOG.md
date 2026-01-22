<!-- markdownlint-disable MD024 (no-duplicate-header) -->

# Changelog 🧾

## 15.2.3

### Changes

* 7c8e1ab: relax constraints for [python-imcflibs] to include major release 2.x

## 15.2.2

Most of the changes for this version were related to publishing the package not
only as a mavenized `.jar` on SciJava, but also as a [Python `.whl` on
PyPI][pypi_whl] using [Poetry].

### Fixes

* 7e02b2e: fix ConfigParser import for Python 3
* 73fad94: fix StringIO import for Python 3

## 15.2.1

### Fixes

* 9f21176: add a workaround for an ImageJ Macro `return` statement weirdness

## 15.2.0

### Changes

* 2988061: import submodules automatically, so any part of the package can be
  accessed with a simple import micrometa and then using the fully qualified
  name of a function

## 15.1.0

### Changes

* 5ec0e9c: make `dname` parameter optional in `imagej.write_stitching_macro()`
* cc066a8: update dependencies for [python-imcflibs] and [jython-olefile].

[python-imcflibs]: https://github.com/imcf/python-imcflibs
[jython-olefile]: https://github.com/imcf/jython-olefile
[pypi_whl]: https://pypi.org/project/python-micrometa/
[Poetry]: https://python-poetry.org/
