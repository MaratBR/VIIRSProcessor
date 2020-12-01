import inspect
from datetime import datetime

import gdal
import numpy as np

from typing import List, Tuple, Optional

import pyproj
from loguru import logger

from gdal_viirs.const import GIMGO, is_nodata, ND_OBPT, PROJ_LCC, ND_NA
from gdal_viirs.types import ProcessedBandsSet, GeofileInfo, ProcessedFileSet, Point, Number, \
    ProcessedGeolocFile, ProcessedBandFile, ViirsFileSet
from gdal_viirs.utility import require_driver, gdal_read_subdataset, gdal_open, h5py_get_dataset


def get_projection(proj) -> pyproj.Proj:
    proj = proj or PROJ_LCC
    return pyproj.Proj(proj)


def trim_data(arr: np.ndarray, trim_value=None,
              ret_mask=False, ret_offset=False) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Point]]:
    """
    Обрезает nodata сверху и снизу
    """
    if inspect.isfunction(trim_value):
        mask = trim_value(arr)
    else:
        mask = is_nodata(arr) if trim_value is None else arr == trim_value
    offset = None
    mask = ~np.all(mask, axis=1)
    if ret_offset:
        line_idx = np.where(mask)[0]
        offset = Point(0, np.min(line_idx))
    return arr[mask], mask if ret_mask else None, offset if ret_offset else None


def fill_nodata(arr: np.ndarray, nd_value=ND_OBPT, smoothing_iterations=5,
                max_search_dist=100):
    memfile = require_driver('MEM').Create('', arr.shape[1], arr.shape[0], 1, gdal.GDT_UInt16)
    memfile.GetRasterBand(1).SetNoDataValue(nd_value)
    memfile.GetRasterBand(1).WriteArray(arr)
    result = gdal.FillNodata(
        targetBand=memfile.GetRasterBand(1),
        maskBand=None,
        maxSearchDist=max_search_dist,
        smoothingIterations=smoothing_iterations
    )
    assert result == 0, f'FillNodata failed, error code: {result}'
    arr = memfile.GetRasterBand(1).ReadAsArray()
    return arr


def hlf_process_geoloc_file(geofile: GeofileInfo, scale: Number, lat_dataset='Latitude',
                            lon_dataset='Longitude', proj=None) -> Optional[ProcessedGeolocFile]:
    """
    Обробатывает файл геолокаци, на данный момент поддерживается только GIMGO
    """

    projection = get_projection(proj)
    logger.info('ОБРАБОТКА ' + geofile.name)
    gdal_file = gdal_open(geofile)
    lat = gdal_read_subdataset(gdal_file, lat_dataset).ReadAsArray()
    lon = gdal_read_subdataset(gdal_file, lon_dataset).ReadAsArray()
    logger.debug(f'lat.shape={lat.shape} lon.shape={lon.shape}')
    lonlat_mask = (lon > -200) * (lat > -200)
    nodata_values = len(lonlat_mask[lonlat_mask == False])
    logger.debug(f'Обнаружено {nodata_values} значений nodata в массивах широты и долготы')

    lat_masked = lat[lonlat_mask]
    lon_masked = lon[lonlat_mask]

    started_at = datetime.now()
    logger.info('ПРОЕКЦИЯ...')
    x_index, y_index = projection(lon_masked, lat_masked)
    logger.info(f'ПРОЕКЦИЯ. ГОТОВО: {(datetime.now() - started_at).seconds}s')
    assert x_index.shape == y_index.shape, 'x_index.shape != y_index.shape'
    assert np.all(np.isfinite(x_index)), 'x_index contains non-finite numbers'
    assert np.all(np.isfinite(x_index)), 'y_index contains non-finite numbers'
    x_index, y_index = np.int_(x_index), np.int_(y_index)

    x_min = x_index.min()
    y_max = y_index.max()

    logger.info('ОБРАБОТКА ЗАВЕРШЕНА ' + geofile.name)
    return ProcessedGeolocFile(info=geofile, lat=lat, lon=lon, x_index=x_index, y_index=y_index,
                               lonlat_mask=lonlat_mask, geotransform_max_y=y_max, geotransform_min_x=x_min,
                               projection=projection, scale=scale)


def hlf_process_band_file(geofile: GeofileInfo, geoloc_file: ProcessedGeolocFile) -> Optional[ProcessedBandFile]:
    """
    Обрабатывает band-файл
    """
    _require_band_notimpl(geofile)

    logger.info(f'ОБРАБОТКА {geofile.band_verbose}: {geofile.name}')
    time = datetime.now()

    f = gdal_open(geofile)
    dataset_name = geofile.get_band_dataset()
    sub = gdal_read_subdataset(f, dataset_name)
    arr = sub.ReadAsArray()
    arr = arr[geoloc_file.lonlat_mask]

    # TODO оптимизировать (это можно просто заранее вычислить)
    x_index = np.int_(geoloc_file.x_index / geoloc_file.scale)
    y_index = np.int_(geoloc_file.y_index / geoloc_file.scale)

    assert x_index.shape == arr.shape, 'x_index.shape != arr.shape'
    assert y_index.shape == arr.shape, 'y_index.shape != arr.shape'

    x_index -= np.min(x_index)
    y_index -= np.min(y_index)
    image_shape = (np.max(y_index) + 1, np.max(x_index) + 1)
    logger.debug(f'hlf_process_band_file: image_shape={image_shape}')
    assert len(image_shape) == 2
    assert all(d > 1 for d in image_shape)

    image = np.zeros(image_shape, 'uint16') + ND_NA
    image[y_index, x_index] = arr
    del arr
    image = np.flip(image, 0)
    image = fill_nodata(image)
    image = np.float_(image)
    # Поменять nodata на nan, применить ReflectanceFactors
    mask = is_nodata(image)
    image[mask] = np.nan

    data = h5py_get_dataset(geofile.path, dataset_name + "Factors")
    if data is not None:
        mask = ~mask
        image[mask] *= data[0]
        image[mask] += data[1]
    else:
        logger.warning('Не удалось получить ' + dataset_name + "Factors")
    time = datetime.now() - time
    logger.info(f'ОБРАБОТАН {geofile.band_verbose}: {time.microseconds / 1000}ms')
    return ProcessedBandFile(data=image, geoloc_file=geoloc_file)


def hlf_process_fileset(fileset: ViirsFileSet, scale=15000, do_trim=False, proj=None) -> Optional[ProcessedFileSet]:
    if len(fileset.band_files) == 0:
        raise ValueError('Band-файлы не найдены')
    logger.info(f'Обработка набора файлов {fileset.geoloc_file.name} scale={scale}')
    geoloc_file = hlf_process_geoloc_file(fileset.geoloc_file, scale, proj=proj)
    if geoloc_file is None:
        return None
    required_width = -1
    required_height = -1

    band_files = _hlf_process_band_files(geoloc_file, fileset.band_files, do_trim)
    # Теперь нужно изменить размер каждого band'а, так чтобы он был минимальный, но одинаковый для всех band'ов
    if do_trim:
        for i in range(len(fileset.band_files)):
            if fileset.band_files[i] is None:
                continue
            processed, offset = band_files[i]
            processed.data = np.pad(processed, (
                (offset.y, required_height - offset.y - processed.data.shape[0]),
                (offset.x, required_width - offset.x - processed.data.shape[1])), constant_values=(np.nan,))
    return ProcessedFileSet(geoloc_file=geoloc_file, bands_set=band_files)


def _hlf_process_band_files(geoloc_file: ProcessedGeolocFile,
                            files: List[GeofileInfo],
                            do_trim: bool) -> ProcessedBandsSet:
    results = []

    required_width = -1
    required_height = -1

    assert len(files) > 0, 'bands list is empty'
    assert len(set(b.band for b in files)) == 1, 'bands passed to _hlf_process_band_files belong to different band types'

    resolution = 371 if files[0].band == 'I' else 750

    for file in files:
        processed = hlf_process_band_file(
            file,
            geoloc_file
        )
        if processed is None:
            results.append(None)
            continue

        # TODO trim_data по горизонтали

        if do_trim:
            processed.data, _, offset = trim_data(processed.data, trim_value=np.isnan, ret_offset=True)
        else:
            offset = Point(0, 0)

        required_width = max(required_width, processed.data.shape[1] + offset.x)
        required_height = max(required_height, processed.data.shape[0] + offset.y)

        results.append((processed, offset))

    geotransform = [
        geoloc_file.geotransform_min_x,
        geoloc_file.scale,
        0,
        geoloc_file.geotransform_max_y,
        0,
        -geoloc_file.scale
    ]
    return ProcessedBandsSet(bands=results, geotransform=geotransform, band=files[0].band)


def _require_file_type_notimpl(info: GeofileInfo, type_: str):
    if info.file_type != GIMGO:
        logger.error('Поддерживаются только файлы типа ' + type_)
        raise NotImplementedError('Поддерживаются только файлы типа ' + type_)


def _require_band_notimpl(info: GeofileInfo):
    if not info.is_band:
        logger.error('Поддерживаются только band-файлы')
        raise AssertionError('Поддерживаются только band-файлы')

