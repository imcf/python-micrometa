"""Tools to process data produced with Olympus FluoView."""

import xml.etree.ElementTree as etree

from .log import LOG as log
from .experiment import MosaicExperiment
from .dataset import MosaicDataCuboid, ImageDataOIF, ImageDataOIB, ImageDataOIR


class FluoView3kMosaic(MosaicExperiment):

    """Object representing a tiled project from Olympus FluoView 3000.

    Olympus FluoView 3000 creates a "matl.omp2info" (with "MATL" standing for
    "Multi Area Time Lapse") file for each tiled project.
    The file contains XML (without specifications and without valid namespace
    references), describing some generic settings like tile overlap, number of
    mosaics, and some more.
    After the generic section, every mosaic (a set of tiles belonging together,
    in FV3000 terminology a "group") is described with little detail - basically
    just the filenames of the tiles (".oir") and their position in a fixed
    tile-grid. All other information has to be extracted from the OIR files for
    being able to put the tiles into their correct relation.

    Please note that multiple mosaics ("groups") are contained in these project
    files and each of the mosaics might have different properties.

    Example
    -------
    >>> import microscopy.fluoview
    >>> from log import set_loglevel
    >>> set_loglevel(1)
    >>> mos3k = microscopy.fluoview.FluoView3kMosaic('matl.omp2info')
    """

    def __init__(self, infile, runparser=True, assume_same_size=True):
        """Initialize the object from a "matl.omp2info" XML file.

        Instance Variables
        ------------------
        ns_base : str
            The base URI used in the XML namespace definitions.
        xsi : str
            The XML Schema Instance.
        xmlns : dict
            A dict with the namespaces prefixes required to parse the XML.
        tree : xml.etree.ElementTree
            The parsed XML element tree.
        """
        log.info("Creating FluoView3kMosaic object from [%s]...", infile)
        super(FluoView3kMosaic, self).__init__(infile)
        # define the XML namespaces / prefix map:
        self.tile_size = {
            "X": -1,
            "Y": -1,
        }
        self.common_tile_size = assume_same_size
        self.ns_base = "http://www.olympus.co.jp/hpf"
        self.xsi = "{http://www.w3.org/2001/XMLSchema-instance}"
        self.xmlns = {
            "matl": "%s/protocol/matl/model/matl" % self.ns_base,
            "marker": "%s/model/marker" % self.ns_base,
        }
        self.tree = self.validate_xml()
        self.mosaictrees = self.find_matrix_roi_groups()
        if runparser:
            self.add_mosaics()
        log.debug("FluoView3kMosaic initialization completed.")

    def validate_xml(self):
        """Check XML for being a valid FluoView 3000 mosaic experiment.

        Evaluate the XML tree for known elements like the root tag and some of
        the direct children to make sure the parsed file is in fact a FluoView
        Multi Area Time Lapse XML file. Raises exceptions in case something
        expected can't be found in the tree.

        Returns
        -------
        tree : xml.etree.ElementTree
        """
        rt_expected = "{%s/protocol/matl/model/matl}properties" % self.ns_base
        log.debug("Validating FluoView 3000 MATL XML (%s)", self.infile["full"])
        tree = etree.parse(self.infile["full"])
        root = tree.getroot()
        log.debug('Checking XML root tag to be "%s"', rt_expected)
        if not root.tag == rt_expected:
            raise TypeError("Invalid XML root tag: %s" % root.tag)
        att = root.attrib
        log.debug("Multi Area Time Lapse properties:")
        log.debug(" - version: %s", att["version"])
        log.debug(" - application version: %s", att["applicationVersion"])
        log.debug(" - platform version: %s", att["platformVersion"])
        log.debug(" - id: %s", root.attrib["id"])
        if not root.attrib["version"] == "2.2":
            raise ValueError("Unknown properties version: %s" % att["version"])

        stage = root.find("matl:stage", self.xmlns)
        stage_name = stage.find("matl:name", self.xmlns).text
        if not stage_name == "PRIOR,H101F":
            raise ValueError("Unknown stage found: %s" % stage_name)
        log.debug("Correct stage found (%s).", stage_name)
        overlap = int(stage.find("matl:overlap", self.xmlns).text)
        log.debug("Found stage overlap to be %s.", overlap)
        self.supplement["overlap"] = overlap

        log.info("Finished validating XML.")
        return tree

    def find_matrix_roi_groups(self):
        """Locate potential 'MatrixROI' trees within the XML.

        A tiled dataset is defined as a 'matl:group' of type
        'matl:DefineMatrixROI' in the omp2info file.
        """
        matrix_groups = list()

        log.debug("Looking for Matrix ROI groups (tiling datasets).")
        root = self.tree.getroot()
        groups = root.findall("matl:group", self.xmlns)
        for grp in groups:
            grp_type = grp.attrib[self.xsi + "type"]
            if grp_type == "matl:DefineMatrixROI":
                log.debug("Group %s is a Matrix ROI.", grp.attrib["objectId"])
                matrix_groups.append(grp)
            if grp_type == "matl:MosaicROI":
                log.debug("Group %s is a Mosaic ROI.", grp.attrib["objectId"])
                matrix_groups.append(grp)

        log.info("Found %i Matrix ROIs (tiling datasets).", len(matrix_groups))
        return matrix_groups

    def add_mosaics(self):
        """Run the parser for all relevant XML subtrees."""
        for i, tree in enumerate(self.mosaictrees):
            try:
                self.add_mosaic(tree, i)
            except ValueError as err:
                log.warn("Skipping mosaic %s: %s", i, err)
            except RuntimeError as err:
                log.warn("Error parsing mosaic %s, SKIPPING: %s", i, err)
                continue

    def add_mosaic(self, tree, index=-1):
        """Parse one mosaic XML and create a MosaicDataset from it.

        Parameters
        ----------
        tree : xml.etree.ElementTree.Element
        index : int
            The index number of the mosaic, to be set in its supplementary dict.
        """
        mosaic_ds = self.parse_mosaic(tree)
        mosaic_ds.supplement["index"] = index
        self.add_dataset(mosaic_ds)

    def parse_mosaic(self, tree):
        """Parse an XML subtree and create a MosaicDataset from it.

        Parameters
        ----------
        tree : xml.etree.ElementTree.Element

        Returns
        -------
        mosaic_ds : MosaicDataCuboid
            The mosaic dataset object for this tree.
        """
        # lambda functions for tree.find().text and int/float conversions:
        tft = lambda t, p: t.find(p, self.xmlns).text
        tfi = lambda t, p: int(tft(t, p))

        oid = tree.attrib["objectId"]
        log.info("Processing ROI group %s...", oid)

        # investigate the ROI info section ("marker:regionInfo")
        roii = tree.find("marker:regionInfo", self.xmlns)
        roii_type = roii.attrib[self.xsi + "type"]
        if (
            not roii_type == "marker:rectangleRegion"
            and not roii_type == "marker:polygonRegion"
        ):
            msg = 'Group <%s>: unsupported region type "%s".' % (oid, roii_type)
            log.warn(msg)
            raise NotImplementedError(msg)
        assert tft(roii, "marker:shape") in ["Rectangle", "Polygon"]
        log.debug("Region shape: %s", tft(roii, "marker:shape"))

        # further investigate the group section ("marker:regionInfo")
        if not tft(tree, "matl:enable") == "true":
            msg = 'Group <%s> marked as "disabled".' % oid
            log.warn(msg)
            raise ValueError(msg)
        gid = tft(tree, "matl:protocolGroupId")
        log.debug(' - group ID: "%s"', gid)

        areai = tree.find("matl:areaInfo", self.xmlns)
        count = {
            "x": tfi(areai, "matl:numOfXAreas"),
            "y": tfi(areai, "matl:numOfYAreas"),
        }
        # tile sizes are stored in areaWidth/areaHeight in nanometers:
        log.debug(" - number of areas X / Y: %s / %s", count["x"], count["y"])
        log.debug(
            " - tile size: %s x %s nm",
            tfi(areai, "matl:areaWidth"),
            tfi(areai, "matl:areaHeight"),
        )

        areas = tree.findall("matl:area", self.xmlns)
        log.info("Found %s area sections (i.e. tiles).", len(areas))

        mosaic_ds = self.assemble_mosaic_ds(areas, count)
        mosaic_ds.supplement["oid"] = oid
        mosaic_ds.supplement["gid"] = gid
        return mosaic_ds

    def assemble_mosaic_ds(self, areas, count):
        """Assemble a MosaicDataCuboid from the related area subtrees.

        Parameters
        ----------
        areas : list(xml.etree.ElementTree.Element)
            A list of area elements (XML subtrees) of this mosaic.
        count : dict
            A dict (keys 'x' and 'y') with the number of areas in X and Y.

        Returns
        -------
        mosaic_ds : MosaicDataCuboid
            The assembled dataset. Exceptions are raised in case of errors.
        """
        # the FluoView 3000 MATL projects don't have separate project files per
        # mosaic, so we're using the project infile for the mosaic_ds as well:
        mosaic_ds = MosaicDataCuboid(
            "tree", self.infile["orig"], (count["x"], count["y"], 1)
        )
        mosaic_ds.set_overlap(self.supplement["overlap"], "pct")

        for area in areas:
            try:
                log.debug("Trying to parse sub-volume %s", area)
                mosaic_ds.add_subvol(self.parse_area(area))
            except IOError as err:
                msg = "Group has broken image data: %s" % err
                log.error(msg)
                log.info(
                    "Corresponding XML section:\n----\n%s\n----",
                    etree.tostring(area, "utf-8"),
                )
                raise IOError(msg)
            except Exception as err:  # pylint: disable=broad-except
                # catching all other *exceptions* like this is fine since we
                # anyway just skip this mosaic entirely in that case:
                msg = "Unexpected parsing error: %s" % err
                log.error(msg)
                log.info(
                    "Corresponding XML section:\n----\n%s\n----",
                    etree.tostring(area, "utf-8"),
                )
                raise RuntimeError(msg)
        return mosaic_ds

    def parse_area(self, tree):
        """Parse a "matl:area" XML tree and create an ImageData object from it.

        Parameters
        ----------
        tree : xml.etree.ElementTree.Element
            A "matl:area" subtree from a "matl.omp2info" XML file.

        Returns
        -------
        subvol_ds : ImageDataOIR
            A sub-volume dataset built from the information found in the parsed
            XML and the related image file specified therein.
        """
        # lambda functions for tree.find().text and int/float conversions:
        tft = lambda t, p: t.find(p, self.xmlns).text
        tfi = lambda t, p: int(tft(t, p))

        try:
            # ImageData section:
            fname = tft(tree, "matl:image")
            grid_x = tfi(tree, "matl:xIndex")
            grid_y = tfi(tree, "matl:yIndex")
            log.debug('File "%s" grid position: %s / %s', fname, grid_x, grid_y)
            subvol_ds = ImageDataOIR(self.infile["path"] + fname)
            # we don't have the stage coordinates anywhere, so set them to None:
            subvol_ds.set_stagecoords((None, None))
            subvol_ds.set_tilenumbers(grid_x, grid_y)
            if self.common_tile_size:
                if self.tile_size["X"] == -1 or self.tile_size["Y"] == -1:
                    self.tile_size = subvol_ds.get_dimensions()
                    log.warn(
                        "Using common tile size %sx%s",
                        self.tile_size["X"],
                        self.tile_size["Y"],
                    )
                subvol_ds._dim = self.tile_size
            subvol_ds.set_relpos(self.supplement["overlap"])
        except Exception as err:
            log.error("Error parsing XML from OIR: %s", err)
            raise IOError(err)

        log.info(
            'Parsed "%s", positions: grid=[%s/%s] relative=%s',
            fname,
            grid_x,
            grid_y,
            subvol_ds.position["relative"],
        )
        return subvol_ds

    def summarize(self):
        """Generate human readable details about the parsed mosaics."""
        # NOTE: should be moved to abstract superclass
        failcount = len(self.mosaictrees) - len(self)
        msg = "Parsed %i mosaics from the FluoView project.\n\n" % len(self)
        if failcount > 0:
            msg += (
                "\n==== WARNING ====== WARNING ====\n\n"
                "Parsing failed on %i mosaic(s). Missing files?\n "
                "\n==== WARNING ====== WARNING ====\n\n\n" % failcount
            )
        for mos in self:
            msg += "Mosaic %i: " % mos.supplement["index"]
            msg += "%i x %i tiles, " % (mos.dim["X"], mos.dim["Y"])
            msg += "%.1f%% overlap.\n" % mos.get_overlap()
        return msg


class FluoViewMosaic(MosaicExperiment):

    """Object representing a tiled ("mosaic") project from Olympus FluoView.

    Olympus FluoView creates a "MATL_Mosaic.log" (with "MATL" standing for
    "Multi Area Time Lapse") file for each tiled project.
    The file contains XML (no specifications given), describing some generic
    settings like axis directions, number of mosaics, and some more.
    After the generic section, every mosaic (a set of tiles belonging together)
    is described in detail (number of tiles in x and y direction, overlap,
    stage positions, file names and positions of each of the mosaic's tiles).

    Please note that multiple mosaics are contained in these project files and
    each of the mosaics can have different properties.

    Example
    -------
    >>> import microscopy.fluoview as fv
    >>> import microscopy.imagej as ij
    >>> from log import set_loglevel
    >>> set_loglevel(3)
    >>> mosaic = fv.FluoViewMosaic('TESTDATA/OIFmosaic/MATL_Mosaic.log')
    >>> len(mosaic)
    1
    >>> mosaic.supplement['xdir']
    'LeftToRight'
    >>> mosaic[0].dim
    {'Y': 2, 'X': 2, 'Z': 1}
    >>> mosaic[0].subvol[0].storage['dname']
    'Slide1sec001'
    >>> mosaic[0].subvol[0].storage['fname']
    'Slide1sec001_01.oif'
    >>> dname = mosaic[0].storage['path']
    >>> ij.write_all_tile_configs(mosaic)
    >>> code = ij.gen_stitching_macro_code(mosaic, 'stitching')
    >>> ij.write_stitching_macro(code, 'stitch_all.ijm', dname)
    """

    def __init__(self, infile, runparser=True):
        """Parse all required values from the XML file.

        Instance Variables
        ------------------
        tree : xml.etree.ElementTree
        supplement : {'mcount': int, # highest index reported by FluoView
                      'xdir': str,   # X axis direction
                      'ydir': str    # Y axis direction
                     }

        Parameters
        ----------
        runparser : bool (optional)
            Determines whether the tree should be parsed immediately.
        """
        super(FluoViewMosaic, self).__init__(infile)
        self.tree = self.validate_xml()
        self.mosaictrees = self.find_mosaictrees()
        if runparser:
            self.add_mosaics()

    def validate_xml(self):
        """Parse and check XML for being a valid FluoView mosaic experiment.

        Evaluate the XML tree for known elements like the root tag (expected to
        be "XYStage", and some of the direct children to make sure the parsed
        file is in fact a FluoView mosaic XML file. Raises exceptions in case
        something expected can't be found in the tree.

        Returns
        -------
        tree : xml.etree.ElementTree
        """
        log.info("Validating FluoView Mosaic XML...")
        tree = etree.parse(self.infile["full"])
        root = tree.getroot()
        if not root.tag == "XYStage":
            raise TypeError("Unexpected value: %s" % root.tag)
        # find() raises an AttributeError if no such element is found:
        xdir = root.find("XAxisDirection").text
        ydir = root.find("YAxisDirection").text
        # WARNING: 'mcount' is the HIGHEST INDEX number, not the total count!
        mcount = int(root.find("NumberOfMosaics").text)
        # currently we only support LTR and TTB experiments:
        if xdir != "LeftToRight" or ydir != "TopToBottom":
            raise TypeError("Unsupported Axis configuration")
        self.supplement = {"xdir": xdir, "ydir": ydir, "mcount": mcount}
        log.info("Finished validating XML.")
        return tree

    def find_mosaictrees(self):
        """Locate potential mosaics within the XML tree."""
        trees = self.tree.getroot().findall("Mosaic")
        log.info("Found %i potential mosaics in XML.", len(trees))
        return trees

    def add_mosaics(self):
        """Run the parser for all relevant XML subtrees."""
        for tree in self.mosaictrees:
            self.add_mosaic(tree, -1)

    def add_mosaic(self, tree, index=-1):
        """Parse an XML subtree and create a MosaicDataset from it.

        Parameters
        ----------
        tree : xml.etree.ElementTree.Element
        index : int
            The index number of the mosaic, to be set in its supplementary dict.
            Will be parsed from the tree if set to -1.
        """
        # lambda functions for tree.find().text and int/float conversions:
        tft = lambda p: tree.find(p).text
        tfi = lambda p: int(tft(p))
        tff = lambda p: float(tft(p))
        if index == -1:
            index = int(tree.attrib["No"])
        assert tft("XScanDirection") == "LeftToRight"
        assert tft("YScanDirection") == "TopToBottom"

        # assemble the dataset (MosaicDataCuboid):
        # use the infile for the mosaic_ds infile as well as individual
        # mosaics don't have separate project files in our case
        mosaic_ds = MosaicDataCuboid(
            "tree", self.infile["orig"], (tfi("XImages"), tfi("YImages"), 1)
        )
        mosaic_ds.set_overlap(100.0 - tff("IndexRatio"), "pct")
        mosaic_ds.supplement["index"] = index

        # Parsing and assembling the ImageData section should be considered
        # to be moved into a separate method.
        # ImageData section:
        for img in tree.findall("ImageInfo"):
            tft = lambda p: img.find(p).text
            tfi = lambda p: int(img.find(p).text)
            tff = lambda p: float(img.find(p).text)
            subvol_fname = tft("Filename")
            if subvol_fname[-3:] == "oif":
                subvol_reader = ImageDataOIF
            elif subvol_fname[-3:] == "oib":
                subvol_reader = ImageDataOIB
            else:
                raise IOError("Unknown dataset type: %s." % subvol_fname)
            try:
                subvol_ds = subvol_reader(self.infile["path"] + subvol_fname)
                subvol_ds.set_stagecoords((tff("XPos"), tff("YPos")))
                subvol_ds.set_tilenumbers(tfi("Xno"), tfi("Yno"))
                subvol_ds.set_relpos(mosaic_ds.get_overlap("pct"))
                subvol_ds.supplement["index"] = tfi("No")
                mosaic_ds.add_subvol(subvol_ds)
            except IOError as err:
                log.info("Broken/missing image data: %s", err)
                # this subvolume is broken, so we entirely cancel this mosaic:
                mosaic_ds = None
                break
        if mosaic_ds is not None:
            self.add_dataset(mosaic_ds)
        else:
            log.warn("Mosaic %s: incomplete subvolumes, SKIPPING!", index)
            log.warn("First incomplete/missing subvolume: %s", subvol_fname)

    def summarize(self):
        """Generate human readable details about the parsed mosaics."""
        # NOTE: should be moved to abstract superclass
        failcount = len(self.mosaictrees) - len(self)
        msg = "Parsed %i mosaics from the FluoView project.\n\n" % len(self)
        if failcount > 0:
            msg += (
                "\n==== WARNING ====== WARNING ====\n\n"
                "Parsing failed on %i mosaic(s). Missing files?\n "
                "\n==== WARNING ====== WARNING ====\n\n\n" % failcount
            )
        for mos in self:
            msg += "Mosaic %i: " % mos.supplement["index"]
            msg += "%i x %i tiles, " % (mos.dim["X"], mos.dim["Y"])
            msg += "%.1f%% overlap.\n" % mos.get_overlap()
        return msg
