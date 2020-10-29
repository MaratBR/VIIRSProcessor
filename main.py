import os

import gdal

import gdal_viirs as viirs


def main():
    gdal.UseExceptions()
    files = viirs.find_viirs_filesets('/home/marat/Documents/npp', [viirs.GIMGO])
    print(files)
    dataset: viirs.ViirsFileSet = list(files.values())[0]
    processed_fileset = viirs.hlf_process_fileset(dataset)
    viirs.save_as_tiff('/tmp', processed_fileset)


if __name__ == '__main__':
    main()
