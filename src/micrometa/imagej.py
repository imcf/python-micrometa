"""ImageJ related stuff like reading measurement results, etc.

NOTE: This is EXCLUSIVELY intended for functions supporting ImageJ related
operations, like creating stitcher configuration files or such. This package
MUST NOT contain code that only runs WITHIN ImageJ itself, i.e. everything in
the 'micrometa' package must run in plain CPython as well!
"""

from os import listdir
from os.path import join, dirname, basename, splitext

try:
    from imcflibs3.iotools import readtxt
    from imcflibs3.pathtools import exists
except ImportError:
    from imcflibs.iotools import readtxt
    from imcflibs.pathtools import exists


from . import __version__
from .log import LOG as log


def gen_tile_config(mosaic, sort=True, suffix="", force_2d=False):
    """Generate a tile configuration for Fiji's Grid/Collection stitcher.

    Generate a layout configuration file for a ceartain mosaic in the format
    readable by Fiji's "Grid/Collection stitching" plugin. The configuration is
    stored in a file in the input directory carrying the mosaic's index number
    as a suffix.

    Parameters
    ----------
    mosaic : dataset.MosaicData
        The mosaic dataset to generate the tile config for.
    sort : bool, optional
        If set to True the sequence of tiles in the configuration will be
        re-ordered to be line-wise from bottom-right to top-left. This is mostly
        intended for being used with specific fusion methods of the
        Grid/Collection stitcher, e.g. the "Random input tile" where the order
        of the tiles affects the fusion result.
    suffix : str, optional
        An optional suffix to use for the file names in the tile config instead
        of the original one. Can be used if the workflow requires a
        pre-processing step before the actual stitching where results will be
        stored e.g. as ICS files or similar and / or when generating config
        files for stitching projections of the original stacks (e.g. having a
        suffix like "-max.ics").
    force_2d : bool, optional (default=False)
        By setting to True, the configuration will be generated for a 2D mosaic,
        even if the mosaic is a 3D dataset. Can be used to generate a config for
        stitching e.g. projections or single slices of the original stacks.

    Returns
    -------
    config : list(str)
        The tile configuration as a list of strings, one per line.
    """
    log.debug("Mosaic storage path: %s", mosaic.storage["path"])
    tiles = mosaic.files_and_coords(sort)

    conf = [
        "# Generated by %s (%s).\n#\n" % (__name__, __version__),
        "# Define the number of dimensions we are working on\n",
    ]

    # despite a subvolume being a stack (the 'Z' dimension is larger than 1),
    # the coordinates might only be given as a 2D grid, without a z-component -
    # in that case we have to fill in '0' as the z coordinate to make the
    # Grid/Collection stitcher work in 3D:
    coords_are_3d = len(tiles[0][1]) > 2
    log.debug("Tile coordinates are given in 3D: %s", coords_are_3d)

    is_stack = mosaic.subvol[0].get_dimensions()["Z"] > 1
    log.debug("Original dataset is a stack: %s", is_stack)
    is_stack = is_stack and not force_2d
    if is_stack:
        conf.append("dim = 3\n")
        if coords_are_3d:
            coord_format = "(%f, %f, %f)\n"
        else:
            coord_format = "(%f, %f, 0.0)\n"
    else:
        conf.append("dim = 2\n")
        coord_format = "(%f, %f)\n"

    conf.append("# Define the image coordinates (in pixels)\n")
    for tile_details in tiles:
        fname = tile_details[0]
        if suffix:
            try:
                # remove all from the last dot on, then append the new suffix
                fname = fname[: fname.rindex(".")] + suffix
            except ValueError:
                msg = "File name doesn't contain a dot: %s" % fname
                log.error(msg)
                raise ValueError(msg)

        line = "%s; ; " % fname
        line += coord_format % tuple(tile_details[1])

        conf.append(line)

    return conf


def write_tile_config(mosaic, outdir="", padlen=0, suffix="", force_2d=False):
    """Generate and write the tile configuration file.

    Call the function to generate the corresponding tile configuration and
    store the result in a file. The naming scheme is "mosaic_xyz.txt" where
    "xyz" is the zero-padded index number of this particular mosaic.

    Parameters
    ----------
    mosaic : dataset.MosaicData
        The mosaic dataset to write the tile config for.
    outdir : str
        The output directory, if empty the input directory is used.
    padlen : int, optional
        An optional padding length for the index number used in the resulting
        file name, e.g. '2' will result in names like 'mosaic_01.txt' and so on.
    suffix : str, optional
        An optional suffix to be passed on to the gen_tile_config() call.
    force_2d : bool, optional (default=False)
        See gen_tile_config() for details.
    """
    log.info("write_tile_config(%i)", mosaic.supplement["index"])
    config = gen_tile_config(mosaic, suffix=suffix, force_2d=force_2d)
    fname = "mosaic_%0" + str(padlen) + "i%s.txt"
    fname = fname % (mosaic.supplement["index"], suffix)
    if outdir == "":
        fname = join(mosaic.storage["path"], fname)
    else:
        fname = join(outdir, fname)
    with open(fname, "w") as out:
        out.writelines(config)
        log.warn("Wrote tile config to %s", out.name)


def write_all_tile_configs(experiment, outdir="", suffix="", force_2d=False):
    """Wrapper to generate all TileConfiguration.txt files.

    All arguments are directly passed on to write_tile_config().
    """
    padlen = len(str(len(experiment)))
    log.debug("Padding tile configuration file indexes to length %i", padlen)
    for mosaic_ds in experiment:
        write_tile_config(mosaic_ds, outdir, padlen, suffix, force_2d)


def locate_templates(tplpath=""):
    """Locate path to templates, possibly in a .zip or .jar file.

    Parameters
    ----------
    tplpath : str, optional
        The path to a directory or a .zip / .jar file containing the template
        files (the default is '', which will result in the current directory
        being searched for a subdirectory with the name 'ijm_templates').

    Returns
    -------
    tplpath : str
        The path to a directory or .zip / .jar file containing the templates.
    """
    # by default templates are expected in a subdir of the current package:
    if tplpath == "":
        tplpath = join(dirname(__file__), "ijm_templates")
        log.debug("Looking for template directory: %s", tplpath)
        if not exists(tplpath):
            tplpath += ".zip"
            log.debug("Looking for template directory: %s", tplpath)
    # some logic to look for templates in jar files having a version number and
    # possibly a 'SNAPSHOT' part in their filename without having to hard-code
    # those strings here:
    if tplpath.lower().endswith(".jar"):
        candidates = list()
        jar_dir = dirname(tplpath)
        jar_basename = basename(splitext(tplpath)[0])
        for candidate in listdir(jar_dir):
            if candidate.startswith(jar_basename):
                log.debug("Found potential jar for templates: [%s]", candidate)
                candidates.append(candidate)
        candidates.sort()
        log.info("Identified jar for templates: [%s]", candidates[-1])
        tplpath = join(jar_dir, candidates[-1])

    if not exists(tplpath):
        raise IOError("Templates location can't be found!")
    log.info("Templates location: %s", tplpath)
    return tplpath


def gen_stitching_macro(name, path, tplpfx, tplpath="", opts=None):
    """Generate code in ImageJ's macro language to stitch the mosaics.

    Take two template files ("head" and "body") and generate an ImageJ
    macro to stitch the mosaics. Using the splitted templates allows for
    setting default values in the head that can be overridden in this
    generator method (the ImageJ macro language doesn't have a command to
    check if a variable is set or not, it just exits with an error).

    Parameters
    ----------
    name : str
        The dataset name, to be used as a reference in macro log messages.
    path : str
        The path to use as input directory *INSIDE* the macro.
    tplpfx : str
        The prefix for the two template files, will be completed with the
        corresponding suffixes "_head.ijm" and "_body.ijm".
    tplpath : str
        The path to a directory or zip file containing the templates.
    opts : dict (optional)
        A dict with key-value pairs to be put into the macro between the head
        and body to override the macro's default settings.
        NOTE: the values are placed literally in the macro code, this means
        that strings have to be quoted, e.g. opts['foo'] = '"bar baz"'

    Returns
    -------
    ijm : list(str) or str
        The generated macro code as a list of str (one str per line) or as
        a single long string if requested via the "flat" parameter.
    """
    # pylint: disable-msg=E1103
    #   the type of 'ijm' is not correctly inferred by pylint and it complains
    templates = locate_templates(tplpath)
    ijm = []
    ijm.append("// Generated by %s (%s).\n\n" % (__name__, __version__))
    ijm.append("// =================== BEGIN macro HEAD ===================\n")
    ijm += readtxt(tplpfx + "_head.ijm", templates)
    ijm.append("// ==================== END macro HEAD ====================\n")
    ijm.append("\n")

    ijm.append('name = "%s";\n' % name)
    # windows path separator (in)sanity:
    path = path.replace("\\", "\\\\")
    ijm.append('input_dir="%s";\n' % path)
    ijm.append("use_batch_mode = true;\n")
    if opts:
        for option, value in opts.items():
            ijm.append("%s = %s;\n" % (option, value))

    ijm.append("\n")
    ijm.append("// =================== BEGIN macro BODY ===================\n")
    ijm += readtxt(tplpfx + "_body.ijm", templates)
    ijm.append("// ==================== END macro BODY ====================\n")
    log.debug("--- ijm ---\n%s\n--- ijm ---", ijm)
    return ijm


def write_stitching_macro(code, fname, dname=""):
    """Write generated macro code into a file.

    Parameters
    ----------
    code : list(str)
        The code as a list of strings, one per line.
    fname : str
        The desired output filename.
    dname : str (optional)
        The output directory, will be joined with `fname` if specified.
    """
    if dname:
        fname = join(dname, fname)
    log.debug('Writing macro to output directory: "%s".', fname)
    with open(fname, "w") as out:
        out.writelines(code)
        log.warn('Wrote macro template to "%s".', out.name)
