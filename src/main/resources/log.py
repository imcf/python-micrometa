"""A convenience module to set up logging with some default values across
multiple modules.

Example
-------
>>> from log import log

From there on a logger is available for usage with e.g. log.warn(), even if the
import statement from above happens in multiple places across modules, it will
always use the same logger instance (that "singleton" functionality is built
into the logging module, we just do the setup here). This can easily be checked
by looking at the log handlers in the different modules.

The logging levels, in increasing order of importance, are:

DEBUG
INFO
WARN
ERROR
CRITICAL

To set the verbosity level when you're e.g. using argparse to count the number
of occurences of '-v' from the commandline into a variable 'verbosity', this
code can be used:
>>> loglevel = (3 - args.verbosity) * 10
>>> log.setLevel(loglevel)
"""

import logging

log = logging.getLogger('imcf_logger')

# we always log to stdout, so add a console handler to the logger
STREAM_HDL = logging.StreamHandler()
log.addHandler(STREAM_HDL)


def set_loglevel(verbosity):
    """Calculate the default loglevel and set it accordingly.

    This is a convenience function that wraps the calculation and setting of
    the logging level. The way our "log" module is currently built (as a
    singleton), there is no obvious better way to have this somewhere else.

    Example
    =======
    This will set the loglevel to DEBUG:
    >>> set_loglevel(2)

    This will set the loglevel to INFO:
    >>> set_loglevel(1)
    """
    # default loglevel is 30 while 20 and 10 show more details
    loglevel = (3 - verbosity) * 10
    log.setLevel(loglevel)

def set_filehandler(fname, no_stderr=False, mode='a'):
    """Set the logging handler to a FileHandler.

    Optionally removes the StreamHandler that logs to stderr.

    Returns
    -------
    FILE_HDL : FileHandler
    """
    FILE_HDL = logging.FileHandler(fname, mode=mode)
    log.addHandler(FILE_HDL)
    if no_stderr:
        log.removeHandler(STREAM_HDL)
    return FILE_HDL

# from http://stackoverflow.com/questions/4722745
#
# formatter = logging.Formatter(
#     "%(asctime)s %(threadName)-11s %(levelname)-10s %(message)s")
# # Alternative formatting available on python 3.2+:
# # formatter = logging.Formatter(
# #     "{asctime} {threadName:>11} {levelname} {message}", style='{')
#
# # Log to file
# filehandler = logging.FileHandler("debug.txt", "w")
# filehandler.setLevel(logging.DEBUG)
# filehandler.setFormatter(formatter)
# log.addHandler(filehandler)
#
# # Log to stdout too
# streamhandler = logging.StreamHandler()
# streamhandler.setLevel(logging.INFO)
# streamhandler.setFormatter(formatter)
# log.addHandler(streamhandler)
