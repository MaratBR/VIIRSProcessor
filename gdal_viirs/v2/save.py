import os

import gdal
import pyproj.enums
from loguru import logger

from gdal_viirs.v2.types import ProcessedFileSet, ProcessedBandsSet
from gdal_viirs.v2.utility import require_driver


def save_as_tiff(root_path: str,
                 fileset: ProcessedFileSet):
    driver = require_driver('GTiff')
    wkt = fileset.geoloc_file.projection.crs.to_wkt(version=pyproj.enums.WktVersion.WKT1_GDAL)

    filename = os.path.join(root_path, f'{fileset.geoloc_file.info.name}-processed.tiff')
    logger.info('Записываем: ' + filename)
    bands_set: ProcessedBandsSet = fileset.bands_set
    band: gdal.Band = bands_set.bands[0].data_ds.GetRasterBand(1)
    shape = [band.YSize, band.XSize]
    file: gdal.Dataset = driver.Create(filename, shape[1], shape[0], len(bands_set.bands), gdal.GDT_Float32)
    file.SetProjection(wkt)
    file.SetGeoTransform(bands_set.geotransform)
    for bi in range(len(bands_set.bands)):
        processed = bands_set.bands[bi]
        if processed is not None:
            file.GetRasterBand(bi + 1).WriteArray(processed.data)

