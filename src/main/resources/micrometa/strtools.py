"""String related helper functions."""


# this is taken from numpy's iotools:
def _is_string_like(obj):
    """Check whether obj behaves like a string.

    Using this way of checking for a string-like object is more robust when
    dealing with stuff that can behave like a 'str' but is not strictly an
    instance of it (or a subclass thereof). So it's more generic than using
    isinstance(obj, str).

    Example
    -------
    >>> _is_string_like('foo')
    True
    >>> _is_string_like(123)
    False
    """
    try:
        obj + ''
    except (TypeError, ValueError):
        return False
    return True


def filename(name):
    """Get the filename from either a filehandle or a string.

    This is a convenience function to retrieve the filename as a string given
    either an open filehandle or just a plain str containing the name.

    Parameters
    ----------
    name : str or filehandle

    Returns
    -------
    name : str

    Example
    -------
    >>> filename('test_file_name')
    'test_file_name'
    >>> filename(open(__file__, 'r'))
    'strtools.py'
    """
    if isinstance(name, file):
        return name.name
    elif _is_string_like(name):
        return name
    else:
        raise TypeError


def flatten(lst):
    """Make a single string from a list of strings.

    Parameters
    ----------
    lst : list(str)

    Returns
    -------
    flat : str

    Example
    -------
    >>> flatten(('foo', 'bar'))
    'foobar'
    """
    flat = ""
    for line in lst:
        flat += line
    return flat
