import os

import gdal
from loguru import logger

from gdal_viirs.types import ProcessedFileSet
from gdal_viirs.utility import require_driver


def save_as_tiff(root_path: str,
                 fileset: ProcessedFileSet):
    driver = require_driver('GTiff')
    wkt = fileset.geoloc_file.projection.crs.to_wkt()

    filename = os.path.join(root_path, f'{fileset.geoloc_file.info.name}--{fileset.geoloc_file.info.band}')
    logger.info('Записываем: ' + filename)
    bands_set = fileset.bands_set
    shape = bands_set.bands[0][0].data.shape
    file: gdal.Dataset = driver.Create(filename, shape[1], shape[0], len(bands_set.bands), gdal.GDT_Float32)
    file.SetProjection(wkt)
    file.SetGeoTransform(bands_set.geotransform)
    for bi in range(len(bands_set.bands)):
        processed, _ = bands_set.bands[bi]
        file.GetRasterBand(bi + 1).WriteArray(processed.data)

