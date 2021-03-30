# MicroMeta

[//]: # (start-badges)

[//]: # (end-badges)

[![Maven Build Status](https://travis-ci.com/imcf/python-micrometa.svg?branch=master)](https://travis-ci.com/imcf/python-micrometa)
[![DOI](https://zenodo.org/badge/152806738.svg)](https://zenodo.org/badge/latestdoi/152806738)

## Microscopy Metadata processing :coffee: :snake: :microscope:

A Python package to process metadata from various light-microscopy related data
formats. Supports generating [ImageJ][1] macros for stitching mosaics / tilings.
Developed and provided by the [Imaging Core Facility (IMCF)][imcf] of the
Biozentrum, University of Basel, Switzerland.

The code is pure Python and known to work with CPython and Jython, so the
package can also be imported in [ImageJ Jython scripts][2].

## Packaging

The package is intended to be available in two flavours, as a mavenized version
(packaged as a jar) to be used in [ImageJ][1], as well as a "pure" Python
package to be provided through [PyPI][3].

[imcf]: https://www.biozentrum.unibas.ch/imcf
[1]: https://imagej.net
[2]: https://imagej.net/Jython_Scripting
[3]: https://pypi.org/
