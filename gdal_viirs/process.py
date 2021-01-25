import os
from datetime import datetime
from typing import List, Optional, Tuple, Iterable

import numpy as np
import pyproj
import time

import rasterio
import rasterio.fill
import rasterio.crs
import rasterio.warp
import rasterio.features
import shapely as shapely
from loguru import logger

from gdal_viirs import utility
from gdal_viirs.const import GIMGO, ND_OBPT, PROJ_LCC, ND_NA
from gdal_viirs.exceptions import SubDatasetNotFound, InvalidData
from gdal_viirs.types import GeofileInfo, ProcessedFileSet, Number, \
    ProcessedGeolocFile, ProcessedBandFile, ViirsFileset, GDALGeotransformT


_RASTERIO_DEFAULT_META = {
    'driver': 'GTiff',
    'nodata': np.nan,
    'dtype': 'float32'
}


def _fill_nodata(arr: np.ndarray, *, nd_value=ND_OBPT, smoothing_iterations=5,
                 max_search_dist=100):
    return rasterio.fill.fillnodata(arr, arr != nd_value, smoothing_iterations=smoothing_iterations,
                                    max_search_distance=max_search_dist)


def process_fileset(fileset: ViirsFileset, output_file: str, scale=2000, trim=True, proj=None):
    """
    Обрабатывает набор файлов, начиная с файла геолокации (широта/долгота) и затем файлы каналов (SVI/SVM),
    создает файл вида out_ИМЯ_ФАЙЛА_ГЕОЛОКАЦИИ.tiff в папке, указанной в параметре out_dir (если указан filename,
    использует его).

    :param fileset: ViirsFileSet, получаенный через функцию utility.find_sdr_viirs_filesets
    :param scale: масштаб, метров на пиксель (рекомендовано значение 2000, чтобы минимизировать nodata)
    :param proj: проекция в формате WKT, значение по умолчанию - gdal_viirs.const.PROJ_LCC
    """
    if len(fileset.band_files) == 0:
        raise InvalidData('Band-файлы не найдены')
    logger.info(f'Обработка набора файлов {fileset.geoloc_file.name} scale={scale}')

    crs = rasterio.crs.CRS.from_wkt(proj or PROJ_LCC)

    geoloc_file = process_geoloc_file(fileset.geoloc_file, scale, proj=proj)
    height, width = geoloc_file.out_image_shape

    bands = _process_band_files_gen(geoloc_file, fileset.band_files)
    transform = geoloc_file.transform

    if trim:
        # обработаем все файлы и запишем их в MemoryFile
        meta = utility.make_rasterio_meta(height, width, len(fileset.band_files))
        meta.update({
            'transform': geoloc_file.transform,
            'crs': crs
        })
        with rasterio.MemoryFile() as f:
            with f.open(**meta) as ds:
                for index, band in enumerate(bands):
                    ds.write(band.data, index + 1)
                # обрезаем nodata
                transform, data = utility.trim_nodata(ds.read(), geoloc_file.transform)
            height, width = data.shape[1:]
    else:
        data = bands

    meta = utility.make_rasterio_meta(height, width, len(fileset.band_files))
    meta.update({
        'transform': transform,
        'crs': crs
    })
    with rasterio.open(output_file, 'w', **meta) as f:
        for index, processed_band in enumerate(data):
            f.write(processed_band.data, index + 1)


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
                      no_data_threshold: Number = 60000) -> np.ndarray:
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
    logger.debug(f'image_shape={image_shape}')
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

    return image


def _process_band_files_gen(geoloc_file: ProcessedGeolocFile,
                            files: List[GeofileInfo]) -> Iterable[np.ndarray]:
    assert len(files) > 0, 'bands list is empty'
    assert len(
        set(b.band for b in files)) == 1, 'bands passed to _process_band_files_gen belong to different band types'

    for index, file in enumerate(files):
        yield process_band_file(file, geoloc_file)


def process_ndvi(input_file: str, output_file: str, cloud_mask_file: str = None):
    """
    Получает NDVI и записывает его в файл.
    """
    with rasterio.open(input_file) as f:
        svi01, svi02 = f.read(1), f.read(2)
        ndvi = (svi02 - svi01)/(svi01 + svi02)
        if cloud_mask_file:
            with rasterio.open(cloud_mask_file) as cmf:
                try:
                    mask = cmf.read(1) == 4
                    ndvi = utility.apply_mask(ndvi, f.transform, mask, cmf.transform, -2)
                except Exception as exc:
                    logger.warning(f'ошибка при применениии маски облачности к NDVI: {exc}')
        meta = utility.make_rasterio_meta(svi01.shape[0], svi02.shape[1], 1)
        meta.update({
            'transform': f.transform,
            'crs': f.crs
        })

    with rasterio.open(output_file, 'w', **meta) as f:
        f.write(ndvi, 1)


def _require_file_type_notimpl(info: GeofileInfo, type_: str):
    if info.file_type != GIMGO:
        logger.error('Поддерживаются только файлы типа ' + type_)
        raise NotImplementedError('Поддерживаются только файлы типа ' + type_)


def _require_band_notimpl(info: GeofileInfo):
    if not info.is_band:
        logger.error('Поддерживаются только band-файлы')
        raise AssertionError('Поддерживаются только band-файлы')


def process_cloud_mask(input_file: str,
                       output_file: str,
                       proj: str = PROJ_LCC,
                       scale: int = None):

    # открываем файл и читаем данные
    with rasterio.open(input_file) as f:
        crs = rasterio.crs.CRS.from_wkt(proj)
        data = f.read()
        # если crs не отличается ничего не делаем, иначе - сменить проекцию
        if f.crs != crs:
            data, transform = rasterio.warp.reproject(
                data,
                src_transform=f.transform,
                src_crs=f.crs,
                dst_crs=crs,
                dst_resolution=None if scale is None else (scale, scale)
            )
        else:
            transform = f.transform

    # обрезать данные
    transform, data = utility.trim_nodata(data, transform, 0)

    meta = {
        'driver': 'GTiff',
        'count': 1,
        'height': data.shape[1],
        'width': data.shape[2],
        'transform': transform,
        'crs': crs,
        'dtype': rasterio.uint8
    }
    with rasterio.open(output_file, 'w', **meta) as f:
        f.write(data)


def calc_ndvi_dynamics(b1, b2):
    return 100 * (b2 - b1) / b1


def process_ndvi_dynamics(composite_b1_input, composite_b2_input, output_file):
    with rasterio.open(composite_b1_input) as b1_f:
        with rasterio.open(composite_b2_input) as b2_f:
            b1_data = b1_f.read(1)
            b2_data = b2_f.read(1)
            b1_data, b1_transform, b2_data, b2_transform = utility.crop_intersection(
                b1_data, b1_f.transform, b2_data, b2_f.transform)
            mask = (b1_data > 0) * (b2_data > 0)
            b3 = calc_ndvi_dynamics(b1_data, b2_data)
            b3[~mask] = -np.inf

            with rasterio.open(output_file, 'w', driver='GTiff', count=1, crs=b1_f.crs, transform=b1_transform,
                               nodata=np.nan, width=b3.shape[1], height=b3.shape[0], dtype='float32') as out:
                out.write(1, b3)


