print(hr);
print("Stitching macro for dataset [" + name + "]");
// input_dir must not be empty
if (input_dir == '') {
    print(hr);
    print("ERROR: No input directory given, stopping!");
    print(hr);
    exit;
}

setBatchMode(use_batch_mode);

// stitching parameters template
tpl  = "type=[Positions from file] ";
tpl += "order=[Defined by TileConfiguration] ";
tpl += "directory=[" + input_dir + "] ";
tpl += "fusion_method=[Linear Blending] ";
tpl += "regression_threshold=" + stitch_regression + " ";
tpl += "max/avg_displacement_threshold=" + stitch_maxavg_ratio + " ";
tpl += "absolute_displacement_threshold=" + stitch_abs_displace + " ";
tpl += "computation_parameters=";
tpl += "[Save computation time (but use more RAM)] ";
tpl += "image_output=[Fuse and display] ";
if (compute) {
    tpl += "compute_overlap ";
    tpl += "subpixel_accuracy ";
}
if (ignore_z_stage) {
    tpl += "ignore_z_stage ";
}


tileconfigs = get_tileconfig_files(input_dir);
for (i = 0; i < tileconfigs.length; i++) {
    layout_file = tileconfigs[i];
    ds_name = replace(layout_file, '.txt', '');
    ds_name = replace(ds_name, '.ics', '');
    ds_name = replace(ds_name, '.ids', '');
    export_file  = input_dir + '/' + ds_name + export_format;
    preview_file = input_dir + '/' + ds_name + '_preview.jpg';
    param = tpl + "layout_file=[" + layout_file + "]";
    print(hr);
    print("*** [" + name + "]");
    print("*** processing [" + layout_file + "]");
    print("*** preview file [" + preview_file + "]");
    print("*** output file [" + export_file + "]");
    print("*** parameters used: " + param);
    run("Grid/Collection stitching", param);

    // rotate result if requested:
    rotate(rotation_angle);
    
    // export using Bio-Formats:
    bioformats_export(export_file, layout_file);

    // save a JPEG preview and close all images:
    gen_preview_jpeg(preview_file);
}
duration = (getTime() - time_start) / 1000;
print(hr);
print("[" + name + "]: processed " + tileconfigs.length + " mosaics.");
print("Overall duration: " + duration + "s");
print(hr);

// save the "Log" window into a text file:
logmessages = getInfo("log");
fh = File.open(input_dir + '/log_stitching_' + tstamp + '.txt');
print(fh, tstamp); // write the timestamp as first line
print(fh, logmessages);
File.close(fh);

setBatchMode(false);
