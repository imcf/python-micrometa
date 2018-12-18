// default values required to be set:
name = '';  // the dataset name
compute = true;  // whether to compute the overlap
input_dir = '';  // needs to be set later, otherwise macro quits if empty
use_batch_mode = false;
export_format = ".ids";  // usually ".ome.tif" or ".ids"
split_z_slices = false;
rotation_angle = 0;
stitch_regression = 0.3;
stitch_maxavg_ratio = 2.5;
stitch_abs_displace = 3.5;
ignore_z_stage = true;  // resulting z-slices on same levels as input stacks

// shortcuts
// marker for separating log messages
hr = "========================================";  // horizontal rule
hr = hr + hr;


function lpad(str) {
    if (lengthOf("" + str) < 2) {
        str = "0" + str;
    }
    return str;
}


function get_tileconfig_files(dir) {
    /* Generate an array with tile config files.
     *
     * Scan a directory for files matching a certain pattern and assemble a
     * new array with the filenames.
     */
    pattern = 'mosaic_[0-9]+\.txt';
    filelist = getFileList(dir);
    tileconfigs = newArray(filelist.length);
    ti = 0;  // the tileconfig index
    for (fi=0; fi<filelist.length; fi++) {
        if(matches(filelist[fi], pattern)) {
            tileconfigs[ti] = filelist[fi];
            //print(tileconfigs[ti]);
            ti++;
        }
    }
    return Array.trim(tileconfigs, ti);
}


function rotate(rotation_angle) {
    if (rotation_angle > 0) {
        print("*** Rotating image by " + rotation_angle + " deg. clock-wise");
        getDimensions(width, height, channels, slices, frames);
        run("Rotate... ", "angle=" + rotation_angle + " grid=0 interpolation=None enlarge");
        if (rotation_angle == 90 || rotation_angle == 270) {
            if (height > width) {
                top = (height - width + 1) / 2;
                left = 0;
            } else {
                top = 0;
                left = (width - height + 1) / 2;
            }
            makeRectangle(left, top, height, width);
            run("Crop");
        }
    }
}


function bioformats_export(filename, layout_file) {
    // first clean up existing files, otherwise Bio-Formats might create
    // a horrible mess mixing old and new metadata / dimensions:
    _ = File.delete(filename);
    if (endsWith(filename, '.ids')) {
        _ = File.delete(replace(filename, '.ids$', '.ics'));
    }
    bfexp  = "save=[" + filename + "] ";
    if (split_z_slices) {
        bfexp += "write_each_z_section ";
    }
    bfexp += "compression=Uncompressed";
    print("*** [" + name + "]: finished " + layout_file);
    print("*** Exporting to: " + filename);
    run("Bio-Formats Exporter", bfexp);
    print("*** Finished exporting to: " + filename);
}


function gen_preview_jpeg(jpeg_fname) {
    // create a JPEG preview using a max-projection, enhancing contrast for
    // all channels, setting the color mode to "composite" and downscaling the
    // image to have a maximum size of 1024px on its longes axis
    // NOTE: closes all open images!
    getDimensions(width, height, channels, slices, frames);
    if (slices > 1) {
        id = getImageID();
        title = getTitle();
        run("Z Project...", "projection=[Max Intensity]");
        newid = getImageID();
        selectImage(id);
        close();
        selectImage(newid);
    }

    if (channels > 1) {
        for (ch = 1; ch <= channels; ch++) {
            Stack.setChannel(ch);
            run("Enhance Contrast...", "saturated=0.3");
        }
        Stack.setDisplayMode("composite");
    } else {
        run("Enhance Contrast...", "saturated=0.3");
    }

    if (width > 1024 || height > 1024) {
        oldwidth = width;
        oldheight = height;
        if (width > height) {
            height = (height / width) * 1024;
            width = 1024;
        } else {
            width = (width / height) * 1024;
            height = 1024;
        }
        run("Scale...", "x=- y=- width=" + width + " height=" + height + " interpolation=None average");
        makeRectangle((oldwidth-width+1)/2, (oldheight-height+1)/2, width, height);
        run("Crop");
    }
    saveAs("Jpeg", jpeg_fname);
    close();
}


// clear the log window:
print("\\Clear");

// remember starting time to calculate overall runtime
time_start = getTime();
// generate a timestamp string to print into the logfile
getDateAndTime(year, month, dow, dom, hour, minute, second, msec);
tstamp = "" + year + "-" + lpad(month) + "-" + lpad(dom) + "_" +
    lpad(hour) + "-" + lpad(minute);
