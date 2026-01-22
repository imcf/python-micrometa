<!-- markdownlint-disable MD024 (no-duplicate-header) -->

# Changelog 🧾

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
