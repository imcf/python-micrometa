#!/usr/bin/env python

"""Doctest runner for the micrometa package.

Needs to be run from micrometa's parent directory.
"""

if __name__ == "__main__":
    import doctest
    import sys

    VERB = '-v' in sys.argv

    import micrometa
    import micrometa.dataset
    import micrometa.experiment
    import micrometa.fluoview
    import micrometa.imagej
    import micrometa.pathtools
    import micrometa.iotools
    import micrometa.strtools

    doctest.testmod(micrometa, verbose=VERB)
    doctest.testmod(micrometa, verbose=VERB)
    doctest.testmod(micrometa.dataset, verbose=VERB)
    doctest.testmod(micrometa.experiment, verbose=VERB)
    doctest.testmod(micrometa.fluoview, verbose=VERB)
    doctest.testmod(micrometa.imagej, verbose=VERB)
    doctest.testmod(micrometa.pathtools, verbose=VERB)
    doctest.testmod(micrometa.iotools, verbose=VERB)
    doctest.testmod(micrometa.strtools, verbose=VERB)
