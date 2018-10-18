"""Helper functions to work with filenames."""

import platform
from os import sep
import os.path


def parse_path(path):
    """Parse a path into its components.

    If the path doesn't end with the pathsep, it is assumed being a file!
    No tests based on existing files are done, as this is supposed to also work
    on path strings that don't exist on the system running this code.

    Returns
    -------
    parsed = {
        'orig' : str   # string as passed into this function
        'full' : str   # separators adjusted to current platform
        'path' : str   # like previous, up to (including) the last separator
        'dname' : str  # segment between the last two separators (directory)
        'fname' : str  # segment after the last separator (filename)
        'ext' : str    # filename extension, containing max 1 period
    }

    Example
    -------

    >>> path_to_file = pathtools.parse_path('/tmp/foo/file')
    >>> path_to_dir = pathtools.parse_path('/tmp/foo/')

    orig : The full path string as given to this function.
    full : Backslashes replaced by the current separator.

    path : 'full' up to the last separator (included)
    >>> path_to_file['path']
    '/tmp/foo/'
    >>> path_to_dir['path']
    '/tmp/foo/'

    dname : The last directory of the path in 'full'.
    >>> path_to_file['dname']
    'foo'
    >>> path_to_dir['dname']
    'foo'

    fname : The filename of 'full', empty in case of a directory.
    >>> path_to_file['fname']
    'file'
    >>> path_to_dir['fname']
    ''
    """
    parsed = {}
    parsed['orig'] = path
    path = path.replace('\\', sep)
    parsed['full'] = path
    parsed['path'] = os.path.dirname(path) + sep
    parsed['fname'] = os.path.basename(path)
    parsed['dname'] = os.path.basename(os.path.dirname(parsed['path']))
    parsed['ext'] = os.path.splitext(parsed['fname'])[1]
    return parsed


def jython_fiji_exists(path):
    """Wrapper to work around problems with Jython 2.7 in Fiji.

    In current Fiji, the Jython implementation of os.path.exists(path) raises a
    java.lang.AbstractMethodError iff 'path' doesn't exist. This function
    catches the exception to allow normal usage of the exists() call.
    """
    try:
        return os.path.exists(path)
    except java.lang.AbstractMethodError:
        return False


# pylint: disable-msg=C0103
#   we use the variable name 'exists' in its common spelling (lowercase), so
#   removing this workaround will be straightforward at a later point
if platform.python_implementation() == 'Jython':
    # pylint: disable-msg=F0401
    #   java.lang is only importable within Jython, pylint would complain
    import java.lang
    exists = jython_fiji_exists
else:
    exists = os.path.exists
