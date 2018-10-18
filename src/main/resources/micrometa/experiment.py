#!/usr/bin/python

"""Tools to process microscopy experiment data."""

from .log import LOG as log
from .pathtools import parse_path


class Experiment(list):

    """Abstract class for generic microscopy experiment data."""

    def __init__(self, infile):
        """Set up the common experiment properties.

        Parameters
        ----------
        infile : str
            The experiment file or folder.

        Instance Variables
        ------------------
        infile : pathtools.parse_path
        datasets : list(Dataset)
        """
        super(Experiment, self).__init__()
        log.info("Creating an 'Experiment' object.")
        self.infile = parse_path(infile)
        log.debug("Experiment original file: %s", self.infile)

    def add_dataset(self, dset):
        """Add a dataset to this experiment."""
        log.debug("Adding a dataset.")
        self.append(dset)


class MosaicExperiment(Experiment):

    """Abstract class for mosaic / tiling experiments."""

    def __init__(self, infile):
        """Set up the common experiment properties.

        Parameters
        ----------
        infile : str
            The experiment file or folder.

        Instance Variables
        ------------------
        supplement : dict
            Keeps supplementary information specific to the mosaic type.
        """
        super(MosaicExperiment, self).__init__(infile)
        self.supplement = {}

    def add_mosaics(self):
        """Abstract method to add mosaics to this experiment."""
        raise NotImplementedError('add_mosaics() not implemented!')
