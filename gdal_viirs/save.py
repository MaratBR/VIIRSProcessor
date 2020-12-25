import os

import gdal
import numpy as np
import pyproj.enums
from loguru import logger

from gdal_viirs.types import ProcessedFileSet, ProcessedBandsSet
from gdal_viirs.utility import require_driver, get_filename


def save_fileset(root_path: str,
                 fileset: ProcessedFileSet,
                 save_ndvi=True):
    """
    В указанной папке создает подпаку с tif-файлом (файлами) с данными

    :param root_path: путь к корневой папке
    :param fileset: набор файлов на охранение
    :param save_ndvi: если True (по-умолчанию) - подсчитывает и сохраняет NDVI в файл вида NDVI_имя_исходного файла
    :return:
    """
    fileset_name = fileset.geoloc_file.info.name_without_extension
    driver = require_driver('GTiff')
    wkt = fileset.geoloc_file.projection.crs.to_wkt(version=pyproj.enums.WktVersion.WKT1_GDAL)

    # Сохраняем основной файл
    filename = os.path.join(root_path, fileset_name + '.tiff')
    bands_set: ProcessedBandsSet = fileset.bands_set
    shape = bands_set.bands[0].data.shape
    file: gdal.Dataset = driver.Create(filename, shape[1], shape[0], len(bands_set.bands), gdal.GDT_Float32)
    assert file is not None, 'не удалось открыть файл: ' + filename
    logger.info('Записываем: ' + filename)
    file.SetProjection(wkt)
    file.SetGeoTransform(bands_set.geotransform)
    for bi in range(len(bands_set.bands)):
        processed = bands_set.bands[bi]
        if processed is not None:
            band: gdal.Band = file.GetRasterBand(bi + 1)
            if bi == 0:
                band.SetNoDataValue(np.nan)
            band.WriteArray(processed.data)

    if save_ndvi and fileset.geoloc_file.info.band == 'I':
        ndvi_file = os.path.join(root_path, get_filename(fileset, 'ndvi'))
        file = driver.Create(ndvi_file, shape[1], shape[0], 1, gdal.GDT_Float32)
        file.SetProjection(wkt)
        file.SetGeoTransform(bands_set.geotransform)
        svi1, svi2 = bands_set.bands[0].data, bands_set.bands[1].data
        ndvi = (svi2 - svi1)/(svi1 + svi2)
        logger.info('Записываем: ' + ndvi_file)
        file.GetRasterBand(1).WriteArray(ndvi)