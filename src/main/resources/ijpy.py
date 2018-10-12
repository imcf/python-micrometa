"""Helper functions for Python code running *inside* ImageJ/Fiji.

This package contains functions and classes that are only useful in the context
of a running Fiji instance as they require the corresponding "ij" packages to
be available. They might also work in plain ImageJ, but this won't be tested at
all.

To use/debug from the Jython Interpreter, use the following commands:

import sys
imcftb = '/opt/imcf_toolbox/'
sys.path.insert(0, imcftb + 'fiji/libs/src')

from log import log
from ijpy import IJLogHandler

ijlogger = IJLogHandler()
log.addHandler(ijlogger)
log.warn('ooomph!')
"""

from ij import IJ
import logging

class IJLogHandler(logging.StreamHandler):

    """A logging handler sending everything to IJ.log()."""

    def emit(self, record):
        """Send a log record to the ImageJ log."""
        IJ.log(self.format(record))
