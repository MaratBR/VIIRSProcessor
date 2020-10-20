import os

import gdal

import gdal_viirs as viirs


def main():
    gdal.UseExceptions()
    files = viirs.find_viirs_filesets('/home/marat/Documents/npp', [viirs.GIMGO])
    geoloc, band_files = list(files.values())[0]
    data = viirs.hlf_process_fileset(geoloc, band_files)
    for d in data:
        viirs.save_as_tiff(os.path.join('/tmp', d[1].name + '.tiff'), d[0])
        print(d)


if __name__ == '__main__':
    main()
