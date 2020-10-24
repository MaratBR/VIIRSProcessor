import os

import gdal

import gdal_viirs as viirs


def main():
    gdal.UseExceptions()
    files = viirs.find_viirs_filesets('/home/marat/Documents/npp', [viirs.GIMGO])
    geoloc, band_files = list(files.values())[0]
    geoloc_processed, data = viirs.hlf_process_fileset(geoloc, band_files)
    data = [arr for (arr, info, offset) in data]
    viirs.save_as_tiff('/tmp/test.tiff', geoloc_processed, data)


if __name__ == '__main__':
    main()
