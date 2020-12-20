from datetime import datetime
from typing import List, Optional, Union, Tuple

import gdal
import numpy as np
import pyproj
import time
from loguru import logger

from gdal_viirs import utility
from gdal_viirs.const import GIMGO, ND_OBPT, PROJ_LCC, ND_NA
from gdal_viirs.exceptions import GDALNonZeroReturnCode, SubDatasetNotFound, InvalidData
from gdal_viirs.types import ProcessedBandsSet, GeofileInfo, ProcessedFileSet, Number, \
    ProcessedGeolocFile, ProcessedBandFile, ViirsFileSet


def fill_nodata(ds_or_arr: Union[np.ndarray, gdal.Dataset], *, nd_value=ND_OBPT, smoothing_iterations=5,
                max_search_dist=100, band_index: int = 1):
    """
    Принимает на вход датасет как класс из GDAL'а или как "сырой массив" numpy, заполняет
    значения nodata используя функцию gdal.FillNodata

    :param ds_or_arr: датасет (класс gdal.Dataset) или массив numpy (ndarray)
    :param nd_value:
        значение nodata.
        Если указано и ds_or_arr - это датасет, сохранит значение nodata из датасета, заменит его на
        указанное значение, а затем, после завершения операции вернет старое значение (если текущее значение
        отличается от указанного)
    :param smoothing_iterations: количество итераций сглаживания
    :param max_search_dist: максимальная дистанция поиска, передаваемая в gdal.FillNodata
    :param band_index: индекс band'а (НАЧИНАЕТСЯ СТРОГО С 1)
    :return: gdal.Dataset если первым аргументом передан gdal.Dataset, иначе numpy массив
    """
    if isinstance(ds_or_arr, np.ndarray):
        arr = ds_or_arr
        ds = utility.create_mem(arr.shape[1], arr.shape[0])
    else:
        ds = ds_or_arr
        arr = None

    band: gdal.Band = ds.GetRasterBand(band_index)
    assert band is not None, f'band №{band_index} не найден'

    if arr is not None:
        # установить значение nd_value как nodata, но только если в функцию был передан массив
        # если был передан уже существующий датасет nd_value будет проигнорировано
        band.SetNoDataValue(nd_value)
        band.WriteArray(arr)

    try:
        code = gdal.FillNodata(
            targetBand=band,
            maskBand=None,
            maxSearchDist=max_search_dist,
            smoothingIterations=smoothing_iterations
        )
        utility.check_gdal_return_code(code)  # выбросит GDALNonZeroReturnCode
    except RuntimeError:  # на случай, если был вызван gdal.UseExceptions()
        raise GDALNonZeroReturnCode(gdal.GetLastErrorNo(), gdal.GetLastErrorMsg())

    if arr is not None:
        result = band.ReadAsArray()
        del band
        del ds
    else:
        result = ds

    return result


def hlf_process_fileset(fileset: ViirsFileSet, scale=2000, proj=None) -> Optional[ProcessedFileSet]:
    """
    Обарабатывает набор файлов с указанным масштабом и проекцией
    :param fileset: ViirsFileSet, получаенный через функцию utility.find_sdr_viirs_filesets
    :param scale: масштаб, который будет в дальнейшем домножен на 351 для I-канала и на 750 для M канала
    :param proj: проекция
    :return:
    """
    if len(fileset.band_files) == 0:
        raise InvalidData('Band-файлы не найдены')
    logger.info(f'Обработка набора файлов {fileset.geoloc_file.name} scale={scale}')
    geoloc_file = hlf_process_geoloc_file(fileset.geoloc_file, scale, proj=proj)
    if geoloc_file is None:
        return None

    band_files = _hlf_process_band_files(geoloc_file, fileset.band_files)
    return ProcessedFileSet(geoloc_file=geoloc_file, bands_set=band_files)


def hlf_process_geoloc_file(geofile: GeofileInfo, scale: Number, lat_dataset='Latitude',
                            lon_dataset='Longitude', proj=None) -> Optional[ProcessedGeolocFile]:
    """
    Обробатывает файл геолокации
    """
    assert geofile.is_geoloc, (
        f'{geofile.name} не является геолокационным файлом, '
        f'поддерживаемые форматы: {", ".join(GeofileInfo.GEOLOC_SDR + GeofileInfo.GEOLOC_EDR)}'
    )
    projection = pyproj.Proj(proj or PROJ_LCC)
    logger.info('ОБРАБОТКА ' + geofile.name)
    gdal_file = utility.gdal_open(geofile)
    lat = utility.gdal_read_subdataset(gdal_file, lat_dataset).ReadAsArray()
    lon = utility.gdal_read_subdataset(gdal_file, lon_dataset).ReadAsArray()
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

    # подсчитывает индексы для пикселей с учетом масштаба
    x_index, y_index = np.int_(x_index / scale), np.int_(y_index / scale)
    x_index -= x_index.min()
    y_index -= y_index.min()

    indexes_ds = utility.create_mem(x_index.shape[0], 2, data=[np.array([x_index, y_index])], dtype=gdal.GDT_UInt32)

    logger.info('ОБРАБОТКА ЗАВЕРШЕНА ' + geofile.name)
    return ProcessedGeolocFile(
        info=geofile,
        lonlat_mask=lonlat_mask,
        geotransform_max_y=y_max,
        geotransform_min_x=x_min,
        projection=projection,
        scale=scale,
        indexes_ds=indexes_ds,
        indexes_count=x_index.shape[0],
        out_image_shape=(y_index.max() + 1, x_index.max() + 1)
    )


def hlf_process_band_file(geofile: GeofileInfo,
                          geoloc_file: ProcessedGeolocFile,
                          store_ds: Optional[gdal.Dataset] = None,
                          band_index: int = 1,
                          no_data_threshold: Tuple[int, int] = (0, 60000)) -> Optional[ProcessedBandFile]:
    """
    Обрабатывает band-файл
    """
    _require_band_notimpl(geofile)

    logger.info(f'ОБРАБОТКА {geofile.band_verbose}: {geofile.name}')
    ts = time.time()

    f = utility.gdal_open(geofile)
    dataset_name = geofile.get_band_dataset()
    sub = utility.gdal_read_subdataset(f, dataset_name)
    arr = sub.ReadAsArray()
    try:
        sdr_mask = utility.gdal_read_subdataset(f, 'BANDSDR', exact_lastname=False).ReadAsArray()
        arr[sdr_mask == 129] = ND_NA
        del sdr_mask
    except SubDatasetNotFound:
        pass
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
    image = fill_nodata(image)
    image = np.float_(image)
    # Поменять nodata на nan
    mask = (image > no_data_threshold[1]) | (image < no_data_threshold[0])
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

    if store_ds is None:
        store_ds = utility.create_mem(image.shape[1], image.shape[0])
        band_index = 1
    store_ds.GetRasterBand(band_index).WriteArray(image)

    return ProcessedBandFile(
        geoloc_file=geoloc_file,
        data_ds=store_ds,
        data_ds_band_index=band_index
    )


def _hlf_process_band_files(geoloc_file: ProcessedGeolocFile,
                            files: List[GeofileInfo]) -> ProcessedBandsSet:
    results = []
    assert len(files) > 0, 'bands list is empty'
    assert len(
        set(b.band for b in files)) == 1, 'bands passed to _hlf_process_band_files belong to different band types'

    bands_store = utility.create_mem(geoloc_file.out_image_shape[1], geoloc_file.out_image_shape[0],
                                     dtype=gdal.GDT_Float64, bands=len(files))

    for index, file in enumerate(files):
        processed = hlf_process_band_file(
            file,
            geoloc_file,
            store_ds=bands_store,
            band_index=index + 1
        )
        results.append(processed)

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
