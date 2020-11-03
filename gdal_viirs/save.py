import os

import gdal
from loguru import logger

from gdal_viirs.types import ProcessedFileSet
from gdal_viirs.utility import require_driver


def save_as_tiff(root_path: str,
                 fileset: ProcessedFileSet):
    driver = require_driver('GTiff')
    wkt = fileset.geoloc_file.projection.crs.to_wkt()

    for band in fileset.bands:
        if band is None:
            continue
        filename = os.path.join(root_path, f'{fileset.geoloc_file.info.name}--{band.band}_BAND.tiff')
        logger.info('Записываем: ' + filename)
        file: gdal.Dataset = driver.Create(
            filename,
            band.bands[0][0].data.shape[1], band.bands[0][0].data.shape[0], len(band.bands), gdal.GDT_Float32)
        file.SetProjection(wkt)
        file.SetGeoTransform(band.geotransform)
        for bi in range(len(band.bands)):
            processed, _ = band.bands[bi]
            file.GetRasterBand(bi + 1).WriteArray(processed.data)

