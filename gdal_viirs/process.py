import os
from datetime import datetime
from typing import List, Optional, Tuple, Iterable

import numpy as np
import pyproj
import time

import rasterio
import rasterio.fill
import rasterio.crs
from loguru import logger

from gdal_viirs import utility
from gdal_viirs.const import GIMGO, ND_OBPT, PROJ_LCC, ND_NA
from gdal_viirs.exceptions import SubDatasetNotFound, InvalidData
from gdal_viirs.types import GeofileInfo, ProcessedFileSet, Number, \
    ProcessedGeolocFile, ProcessedBandFile, ViirsFileSet, GDALGeotransformT
from gdal_viirs.utility import get_filename


_RASTERIO_DEFAULT_META = {
    'driver': 'GTiff',
    'nodata': np.nan,
    'dtype': 'float32'
}


def _fill_nodata(arr: np.ndarray, *, nd_value=ND_OBPT, smoothing_iterations=5,
                 max_search_dist=100):
    """
    :param arr: массив numpy (ndarray)
    :param nd_value: значение nodata
    :param smoothing_iterations: количество итераций сглаживания
    :param max_search_dist: максимальная дистанция поиска, передаваемая в gdal.FillNodata
    :return: numpy массив
    """
    return rasterio.fill.fillnodata(arr, arr != nd_value, smoothing_iterations=smoothing_iterations,
                                    max_search_distance=max_search_dist)


def process_fileset_out(fileset: ViirsFileSet, out_dir: str, filename=None, scale=2000, trim=True, proj=None) -> str:
    """
    Обрабатывает набор файлов, начиная с файла геолокации (широта/долгота) и затем файлы каналов (SVI/SVM),
    создает файл вида out_ИМЯ_ФАЙЛА_ГЕОЛОКАЦИИ.tiff в папке, указанной в параметре out_dir (если указан filename,
    использует его).

    :param filename: имя tiff файла, если не указать имя будет сгенерировано на основании файлас с широтой и долготой
    :param fileset: ViirsFileSet, получаенный через функцию utility.find_sdr_viirs_filesets
    :param scale: масштаб, метров на пиксель (рекомендовано значение 2000, чтобы минимизировать nodata)
    :param proj: проекция в формате WKT, значение по умолчанию - gdal_viirs.const.PROJ_LCC
    :param out_dir: выходная папка
    :return: полный путь к tiff файлу
    """
    if len(fileset.band_files) == 0:
        raise InvalidData('Band-файлы не найдены')
    logger.info(f'Обработка набора файлов {fileset.geoloc_file.name} scale={scale}')
    geoloc_file = process_geoloc_file(fileset.geoloc_file, scale, proj=proj)
    filepath = os.path.join(out_dir, filename or get_filename(fileset))
    height, width = geoloc_file.out_image_shape
    gdal_transform = geoloc_file.geotransform

    bands = _process_band_files_gen(geoloc_file, fileset.band_files)

    if trim:
        gdal_transform, bands = utility.trim_nodata(bands, gdal_transform, scale)
        height, width = bands[0].data.shape

    transform = rasterio.Affine.from_gdal(*gdal_transform)
    meta = utility.make_rasterio_meta(height, width, len(fileset.band_files))

    with rasterio.open(filepath, 'w', **meta) as f:
        f.transform = transform
        f.crs = rasterio.crs.CRS.from_wkt(proj or PROJ_LCC)
        for index, processed_band in enumerate(bands):
            f.write(processed_band.data, index + 1)
    return filepath


def process_geoloc_file(geofile: GeofileInfo, scale: Number, proj=None) -> ProcessedGeolocFile:
    """
    Обробатывает файл геолокации
    """
    assert geofile.is_geoloc, (
        f'{geofile.name} не является геолокационным файлом, '
        f'поддерживаемые форматы: {", ".join(GeofileInfo.GEOLOC_SDR + GeofileInfo.GEOLOC_EDR)}'
    )

    with rasterio.open(geofile.path) as f:
        try:
            lat_dataset = next(ds for ds in f.subdatasets if ds.endswith('/Latitude'))
            lon_dataset = next(ds for ds in f.subdatasets if ds.endswith('/Longitude'))
        except StopIteration:
            raise SubDatasetNotFound('не удалось найти датасеты широты и долготы')

    with rasterio.open(lat_dataset) as lat_ds:
        lat = lat_ds.read(1)

    with rasterio.open(lon_dataset) as lon_ds:
        lon = lon_ds.read(1)

    projection = pyproj.Proj(proj or PROJ_LCC)
    logger.info('ОБРАБОТКА ' + geofile.name)
    logger.debug(f'lat.shape = lon.shape = {lat.shape}')
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
    x_index, y_index = np.int_(np.round(x_index)), np.int_(np.round(y_index))

    x_min = x_index.min()
    y_max = y_index.max()

    # подсчитывает индексы для пикселей с учетом масштаба
    x_index, y_index = np.int_(np.round(x_index / scale)), np.int_(np.round(y_index / scale))
    x_index -= x_index.min()
    y_index -= y_index.min()

    out_image_shape = y_index.max() + 1, x_index.max() + 1

    logger.info('ОБРАБОТКА ЗАВЕРШЕНА ' + geofile.name)
    return ProcessedGeolocFile(
        info=geofile,
        x_index=x_index,
        y_index=y_index,
        lonlat_mask=lonlat_mask,
        geotransform_max_y=y_max,
        geotransform_min_x=x_min,
        projection=projection,
        scale=scale,
        out_image_shape=out_image_shape
    )


def process_band_file(geofile: GeofileInfo,
                      geoloc_file: ProcessedGeolocFile,
                      no_data_threshold: Number = 60000) -> ProcessedBandFile:
    """
    Обрабатывает band-файл
    """
    _require_band_notimpl(geofile)

    logger.info(f'ОБРАБОТКА {geofile.band_verbose}: {geofile.name}')
    ts = time.time()

    dataset_name = geofile.get_band_dataset()
    with rasterio.open(geofile.path) as f:
        try:
            dataset_path = next(ds for ds in f.subdatasets if ds.endswith('/' + dataset_name))
        except StopIteration:
            raise SubDatasetNotFound(dataset_name)

        try:
            sdr_mask = next(ds for ds in f.subdatasets if ds.endswith('BANDSDR'))
            with rasterio.open(sdr_mask) as sdr_mask_f:
                sdr_mask = sdr_mask_f.read(1)
        except StopIteration:
            sdr_mask = None
            pass

    with rasterio.open(dataset_path) as f:
        arr = f.read(1)

    if sdr_mask is not None:
        arr[sdr_mask > 32] = ND_NA
        del sdr_mask

    arr = arr[geoloc_file.lonlat_mask]
    x_index = geoloc_file.x_index
    y_index = geoloc_file.y_index
    assert x_index.shape == arr.shape, f'x_index.shape != arr.shape {x_index.shape} {arr.shape}'
    assert y_index.shape == arr.shape, 'y_index.shape != arr.shape {x_index.shape} {arr.shape}'
    image_shape = geoloc_file.out_image_shape
    logger.debug(f'hlf_process_band_file: image_shape={image_shape}')
    assert len(image_shape) == 2
    assert all(d > 1 for d in image_shape), 'image must be at least 2x2'

    image = np.zeros(image_shape, 'uint16') + ND_NA
    image[y_index, x_index] = arr
    del arr
    image = np.flip(image, 0)
    image = _fill_nodata(image)
    image = image.astype('float32')
    # Поменять nodata на nan
    mask = image > no_data_threshold
    image[mask] = np.nan

    # factors
    data = utility.h5py_get_dataset(geofile.path, dataset_name + "Factors")
    if data is not None:
        mask = ~mask
        image[mask] *= data[0]
        image[mask] += data[1]
    else:
        logger.warning('Не удалось получить ' + dataset_name + "Factors")
    ts = time.time() - ts
    logger.info(f'ОБРАБОТАН {geofile.band_verbose}: {int(ts * 1000)}ms')

    return ProcessedBandFile(
        geoloc_file=geoloc_file,
        data=image
    )


def _process_band_files_gen(geoloc_file: ProcessedGeolocFile,
                            files: List[GeofileInfo]) -> Iterable[ProcessedBandFile]:
    assert len(files) > 0, 'bands list is empty'
    assert len(
        set(b.band for b in files)) == 1, 'bands passed to _hlf_process_band_files belong to different band types'

    for index, file in enumerate(files):
        yield process_band_file(file, geoloc_file)


def process_ndvi(data, fileset: ViirsFileSet, out_dir: str, filename=None) -> str:
    """
    Получает NDVI и записывает его в файл.
    :param data: открытый файл rasterio
    :param fileset: экземпляр ViirsFileSet
    :param out_dir: путь к папке, куда поместить данные
    :param transform: трансформация растера NDVI, обязательно должна быть, если параметр data - это НЕ открытый файл rasterio
    :return: путь к NDVI TIFF файлу
    """
    svi01, svi02 = data.read(1), data.read(2)
    ndvi = (svi02 - svi01)/(svi01 + svi02)
    filepath = os.path.join(out_dir, filename or get_filename(fileset, 'ndvi'))
    meta = utility.make_rasterio_meta(svi01.shape[0], svi02.shape[1], 1)
    meta.update({
        'transform': data.transform,
        'crs': data.crs
    })
    with rasterio.open(filepath, 'w', **meta) as f:
        f.write(ndvi, 1)
    return filepath


def _require_file_type_notimpl(info: GeofileInfo, type_: str):
    if info.file_type != GIMGO:
        logger.error('Поддерживаются только файлы типа ' + type_)
        raise NotImplementedError('Поддерживаются только файлы типа ' + type_)


def _require_band_notimpl(info: GeofileInfo):
    if not info.is_band:
        logger.error('Поддерживаются только band-файлы')
        raise AssertionError('Поддерживаются только band-файлы')
