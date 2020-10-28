import inspect
from typing import List, Dict, Tuple, Union, TypeVar, NamedTuple, Optional

import pyproj
from loguru import logger
import gdal
import numpy as np
from datetime import datetime, time
import os
import re
import h5py

TRIM = False

# region types


DatasetLike = Union[gdal.Dataset, str, 'GeofileInfo']
TNumpyOperable = TypeVar('TNumpyOperable', np.ndarray, float, int)
Number = Union[int, float]


class Point(NamedTuple):
    x: Number
    y: Number


class GeoPoint(NamedTuple):
    lat: Number
    lon: Number


# endregion

# region exception


class ViirsException(Exception):
    def __init__(self, message):
        self.message = message
        super(ViirsException, self).__init__(message)


class DatasetNotFoundException(ViirsException):
    def __init__(self, name):
        super(DatasetNotFoundException, self).__init__(f'Dataset or subdataset {name} not found')
        self.dataset = name


class SubDatasetNotFound(DatasetNotFoundException):
    pass


# endregion

# region constants

ND_NA = 65535
ND_MISS = 65534
ND_OBPT = 65533
ND_OGPT = 65532
ND_ERR = 65531
ND_ELINT = 65530
ND_VDNE = 65529
ND_SOUB = 65528
_ND_MIN_VALUE = 65528


def is_nodata(v):
    return v >= _ND_MIN_VALUE


PROJ_LCC = '''PROJCS["Lambert_Conformal_Conic",
     GEOGCS["GCS_WGS_1984",
         DATUM["WGS_1984",
             SPHEROID["WGS_84",6378137.0,298.252223563]
         ],
         PRIMEM["Greenwich",0.0],
         UNIT["Degree",0.0174532925199433]
     ],
     PROJECTION["Lambert_Conformal_Conic_2SP"],
     PARAMETER["False_Easting",0.0],
     PARAMETER["False_Northing",0.0],
     PARAMETER["Central_Meridian",79.950619],
     PARAMETER["Standard_Parallel_1",67.41206675],
     PARAMETER["Standard_Parallel_2",43.58046825],
     PARAMETER["Scale_Factor",1.0],
     PARAMETER["Latitude_Of_Origin",55.4962675],
     UNIT["Meter",1000]
 ]'''
PROJ_WGS = '''GEOGCS["WGS 84",
DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],
AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]
'''

# endregion

# region utility functions


def require_driver(name: str) -> gdal.Driver:
    driver = gdal.GetDriverByName(name)
    assert driver is not None, f'GDAL driver {name} is required, but missing!'
    return driver


def get_lat_long_data(file: DatasetLike, ret_file: bool = True):
    """
    Открывает датасет для широты и долготы.

    Принимает на вход имя файла или датасет полученный через gdal.Open.
    Возвращает кортеж из 3 элементов: датасет широты, долготы и открытый файл.
    Если ret_file = False, возвращает None вместо файла.
    """
    file = gdal_open(file)
    sub_datasets = file.GetSubDatasets()
    lat_ds = None
    try:
        lat_ds = next(ds_info[0] for ds_info in sub_datasets if 'Latitude' in ds_info[0])
        lat_ds = gdal.Open(lat_ds)
    except StopIteration:
        pass

    lon_ds = None
    try:
        lon_ds = next(ds_info[0] for ds_info in sub_datasets if 'Longitude' in ds_info[0])
        lon_ds = gdal.Open(lon_ds)
    except StopIteration:
        pass

    if lat_ds:
        lat_ds = gdal.Open(lat_ds, gdal.GA_ReadOnly)
    if lon_ds:
        lon_ds = gdal.Open(lon_ds, gdal.GA_ReadOnly)
    return lat_ds, lon_ds, file if ret_file else None


GITCO = 'GITCO'
GMTCO = 'GMTCO'
GIMGO = 'GIMGO'
GMODO = 'GMODO'
GDNBO = 'GDNBO'

GIGTO = 'GIGTO'
GMGTO = 'GMGTO'
GNCCO = 'GNCCO'


class GeofileInfo:
    GEOLOC_SDR = ['GITCO', 'GMTCO', 'GIMGO', 'GMODO', 'GDNBO']
    GEOLOC_EDR = ['GIGTO', 'GMGTO', 'GNCCO']
    GEOLOC = GEOLOC_EDR + GEOLOC_SDR

    I_BAND_SDR__REFLECTANCE = ['SVI01', 'SVI02', 'SVI03']
    I_BAND_SDR__BRIGHT_TEMP = ['SVI04', 'SVI05']
    I_BAND_SDR = I_BAND_SDR__REFLECTANCE + I_BAND_SDR__BRIGHT_TEMP

    M_BAND_SDR__REFLECTANCE = ['SVM01', 'SVM02', 'SVM03', 'SVM04', 'SVM05', 'SVM06', 'SVM07', 'SVM08', 'SVM09', 'SVM10',
                               'SVM11']
    M_BAND_SDR__BRIGHT_TEMP = ['SVM12', 'SVM13', 'SVM14', 'SVM15', 'SVM16']
    M_BAND_SDR = M_BAND_SDR__REFLECTANCE + M_BAND_SDR__BRIGHT_TEMP

    I_BAND_EDR = ['VI1BO', 'VI2BO', 'VI3BO', 'VI4BO', 'VI5BO']
    M_BAND_EDR = ['VM01O', 'VM02O', 'VM03O', 'VM04O', 'VM05O', 'VM06O']

    DNB_SDR = 'SVDNB'
    NCC_EDR = 'VNCCO'

    KNOWN_TYPES = GEOLOC + I_BAND_SDR + M_BAND_SDR + I_BAND_EDR + M_BAND_EDR + [DNB_SDR, NCC_EDR]

    path: str
    name: str
    sat_id: str
    file_type: str
    date: datetime
    t_start: time
    t_end: time
    orbit_number: str
    file_ts: str
    data_source: str

    @staticmethod
    def _parse_time(s: str):
        return time(hour=int(s[:2]), minute=int(s[2:4]), second=int(s[4:6]), microsecond=int(s[6]) * 100000)

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        parts = self.name.split('_', 7)
        self.file_type = parts[0]
        self.sat_id = parts[1]
        self.date = datetime.strptime(parts[2][1:], '%Y%m%d')
        self.t_start = self._parse_time(parts[3][1:])
        self.t_end = self._parse_time(parts[4][1:])
        self.orbit_number = parts[5]
        self.file_ts = parts[6]
        self.data_source = parts[7]

    def __repr__(self):
        if not self.is_known_type:
            info = 'UNKNOWN ' + self.file_type
        else:
            info = f'{self.record_type}, '
            band = self.band
            if band:
                info += 'band=' + band
            else:
                info += 'geoloc'
            info += ', type=' + self.file_type

        return f'<GeofileInfo {info}>'

    @property
    def is_sdr(self):
        return self.record_type == 'SDR'

    @property
    def is_edr(self):
        return self.record_type == 'EDR'

    @property
    def is_band(self):
        return self.band is not None

    @property
    def record_type(self):
        if self.file_type in self.GEOLOC_SDR or \
                self.file_type in self.I_BAND_SDR or \
                self.file_type in self.M_BAND_SDR or \
                self.file_type == self.DNB_SDR:
            return 'SDR'
        if self.file_type in self.GEOLOC_EDR or \
                self.file_type in self.I_BAND_EDR or \
                self.file_type in self.M_BAND_EDR or \
                self.file_type == self.NCC_EDR:
            return 'EDR'
        return None

    @property
    def band(self):
        if self.file_type in self.I_BAND_EDR or self.file_type in self.I_BAND_SDR:
            return 'I'
        if self.file_type in self.M_BAND_EDR or self.file_type in self.M_BAND_SDR:
            return 'M'
        return None

    @property
    def is_known_type(self):
        return self.file_type in self.KNOWN_TYPES

    @property
    def is_geoloc(self):
        return self.file_type in self.GEOLOC


def find_viirs_files(root) -> List[GeofileInfo]:
    """
    Находит и возвращает все HDF VIIRS файлы в указанной папке
    """
    files = os.listdir(root)
    regex = re.compile(r"^[a-zA-Z0-9]+_[a-zA-Z0-9]+_d\d+_t\d+_e\d+_b\d+_c\d+_\w+\.h5$")
    files = filter(lambda filename: regex.match(filename) is not None, files)
    files = map(lambda p: os.path.join(root, p), files)
    files = list(map(GeofileInfo, files))
    return files


def find_viirs_filesets(root, geoloc_types) -> Dict[str, Tuple[GeofileInfo, List[GeofileInfo]]]:
    """
    Возвращает dictionary где ключами являются названия файлов геолокации (с широтой и долготой),
    а занчение - кортеж из двух элементов, первый - информация о файле геолокации, второй - список band-файлов
    """
    result = {}
    files = find_viirs_files(root)
    geoloc_files = list(filter(lambda info: info.file_type in geoloc_types, files))
    for fileinfo in geoloc_files:
        rtype = fileinfo.record_type
        if rtype == 'SDR':
            band_file_types = GeofileInfo.I_BAND_SDR + GeofileInfo.M_BAND_SDR
        elif rtype == 'EDR':
            band_file_types = GeofileInfo.I_BAND_EDR + GeofileInfo.M_BAND_EDR
        band_files = list(filter(
            lambda info:
            info.file_type in band_file_types and
            info.t_start == fileinfo.t_start and
            info.t_end == fileinfo.t_end and
            info.orbit_number == fileinfo.orbit_number,
            files))
        band_files = sorted(band_files, key=lambda f: f.file_type)
        result[fileinfo.name] = fileinfo, band_files
    return result


# endregion

# region alg functions

def get_contrast(arr: np.ndarray, min_val=10000, max_val=60000, colors=255):
    """
    Помещает каждый элемент массива между min_val и max_val в зависимости
    от значения элемента. Использует linspace внутри.

    Не делает различия между nodata и данными.
    """
    mask = (arr >= min_val) * (arr <= max_val)
    colour_gradation = np.linspace(arr[mask].min(), arr[mask].max(), colors)
    contrast = colors - np.searchsorted(colour_gradation, arr)
    return contrast


def get_contrast_preserve_nodata(arr: np.ndarray, min_val=10000, max_val=60000, colors=255, nd_min=65529, nd_max=None):
    """
    Возвращает то же, что и get_contrast, но сохраняет точки nodata неизменными.
    """
    nodata_mask = arr >= nd_min
    if nd_max is not None:
        nodata_mask *= arr <= nd_max
    contrast = get_contrast(arr, min_val, max_val, colors)
    contrast[nodata_mask] = arr[nodata_mask]
    return contrast


# Что это делает?
def get_pass_data(data: np.ndarray, pass_value=0, replacement=255):
    mask = data[:, data.shape[1] // 2] != pass_value
    mask_nancumsum = np.nancumsum(mask)
    mask = (mask_nancumsum != pass_value) * \
           (mask_nancumsum < mask_nancumsum.max()) * \
           (data[:, data.shape[1] // 2] == pass_value)
    data = np.copy(data)
    data[mask] = replacement
    return data


def trim_data(arr: np.ndarray, trim_value=None, ret_mask=False, ret_offset=False) -> Tuple[
    np.ndarray, Optional[np.ndarray], Optional[Point]]:
    """
    Обрезает nodata сверху и снизу
    """
    if inspect.isfunction(trim_value):
        mask = trim_value(arr)
    else:
        mask = arr >= _ND_MIN_VALUE if trim_value is None else arr == trim_value
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


def find_place_stereo(lon_0: Number, lat: TNumpyOperable, lon: TNumpyOperable) -> Tuple[TNumpyOperable, TNumpyOperable]:
    """
    Укра... кхм, позаимствовано из montage_functions.py
    :param lon_0:
    :param lat:
    :param lon:
    :return:
    """
    pi, lat, lon = np.pi, np.radians(lat), np.radians(lon)
    lat_c = np.radians(-89.9999)
    a = 6356773.3
    e = 0.0818191908426215
    lon_0 = np.radians(lon_0)
    d_lon = lon - lon_0
    sin_lat = np.sin(lat)
    sin_lat_c = np.sin(lat_c)
    t = (np.tan(pi / 4 + lat / 2)) / (((1 - e * sin_lat) / (1 + e * sin_lat)) ** (e / 2))
    t_c = (np.tan(pi / 4 + lat_c / 2)) / (((1 - e * sin_lat_c) / (1 + e * sin_lat_c)) ** (e / 2))
    m_c = np.cos(lat_c) * ((1 - (e ** 2) * (sin_lat_c ** 2)) ** (1 / 2))
    ro = (a * m_c * t) / t_c
    return ro * np.sin(d_lon), -ro * np.cos(d_lon)


# endregion

# region "get data" functions


def gdal_open(file: DatasetLike, mode=gdal.GA_ReadOnly) -> gdal.Dataset:
    """
    Открывает hdf5 файл, на вход принимает имя файла, GeofileInfo объект или уже открытый файл.
    В последнем случае, файл не открывается, а просто возвращается назад.
    :param file:
    :param mode:
    :return:
    """
    if isinstance(file, gdal.Dataset):
        return file

    if isinstance(file, GeofileInfo):
        file = file.path
    try:
        f = gdal.Open(file, mode)
    except RuntimeError:
        raise DatasetNotFoundException(file)
    if f is None:
        raise DatasetNotFoundException(file)
    logger.debug(f'mode={_Repr.gdal_access(mode)} file={file} ')
    return f


def gdal_read_subdataset(file: gdal.Dataset, dataset_lastname: str, mode=gdal.GA_ReadOnly) -> gdal.Dataset:
    """
    Прочитывает датасет из другого, родительского, датасета
    :return:
    """
    try:
        name = next(sub[0] for sub in file.GetSubDatasets() if
                    isinstance(sub[0], str) and sub[0].endswith('/' + dataset_lastname))
    except StopIteration:
        raise SubDatasetNotFound(dataset_lastname)
    file = gdal_open(name, mode)
    return file


def h5py_get_dataset(filename: str, dataset_lastname: str):
    f = h5py.File(filename, 'r')
    datasets = []
    f.visit(datasets.append)
    try:
        ds = next(ds for ds in datasets if ds == dataset_lastname or ds.endswith('/' + dataset_lastname))
        data = f[ds][()]
        return data
    except StopIteration:
        return None


# endregion

# region high level functions


class ProcessedGeolocFile(NamedTuple):
    info: GeofileInfo
    lat: np.ndarray
    lon: np.ndarray
    x_index: np.ndarray
    y_index: np.ndarray
    lonlat_mask: np.ndarray
    geotransform: List[Number]
    projection: pyproj.Proj


def hlf_process_geoloc_file(geofile: GeofileInfo, scale: Number, lat_dataset='Latitude',
                            lon_dataset='Longitude') -> ProcessedGeolocFile:
    """
    Обробатывает файл геолокаци, на данный момент поддерживается только GIMGO
    """
    _require_file_type_notimpl(geofile, GIMGO)

    logger.info('ОБРАБОТКА ' + geofile.name)
    gdal_file = gdal_open(geofile)
    v = gdal_file.GetGeoTransform()
    lat = gdal_read_subdataset(gdal_file, lat_dataset).ReadAsArray()
    lon = gdal_read_subdataset(gdal_file, lon_dataset).ReadAsArray()
    logger.debug(f'lat.shape={lat.shape} lon.shape={lon.shape}')
    lonlat_mask = (lon > -200) * (lat > -200)
    nodata_values = len(lonlat_mask[lonlat_mask == False])
    logger.debug(f'Обнаружено {nodata_values} значений nodata в массивах широты и долготы')

    lat_masked = lat[lonlat_mask]
    lon_masked = lon[lonlat_mask]
    lat_min, lat_max = np.min(lat_masked), np.max(lat_masked)
    lon_min, lon_max = np.min(lon_masked), np.max(lon_masked)

    projection = pyproj.Proj(f'''PROJCS["Lambert_Conformal_Conic",
         GEOGCS["GCS_WGS_1984",
             DATUM["WGS_1984",
                 SPHEROID["WGS_84",6378137.0,298.252223563]
             ],
             PRIMEM["Greenwich",0.0],
             UNIT["Degree",0.0174532925199433]
         ],
         PROJECTION["Lambert_Conformal_Conic_2SP"],
         PARAMETER["False_Easting",0.0],
         PARAMETER["False_Northing",0.0],
         PARAMETER["Central_Meridian",79.950619],
         PARAMETER["Standard_Parallel_1",{lat_max}],
         PARAMETER["Standard_Parallel_2",{lat_min}],
         PARAMETER["Scale_Factor",1.0],
         PARAMETER["Latitude_Of_Origin",{(lat_max + lat_min)/2}],
         UNIT["Meter",{scale}]
    ]''')

    use_old = False

    if use_old:
        z = projection(
            [lat_max, lon_min, lon_max, lon_min, lon_max],
            [lat_min, lat_max, lat_max, lat_min, lat_min])
        z = np.array(list(zip(*z)))
        y_min = z[1:4, 1].min()
        x_min, y_max = z[-2, 0], z[1:3, 1].max()
    else:
        z = projection(
            [lon_min, lon_min, lon_max, lon_max],
            [lat_max, lat_min, lat_max, lat_min])
        z = np.array(list(zip(*z)))
        x_min = z[:, 0].min()
        #x_min = z[-1, 0]
        x_max = z[:, 0].max()
        y_max = z[:, 1].max()
        y_min = z[:, 1].min()

    geotransform = [x_min + y_min * scale, scale, 0, y_max * scale, 0, -scale]

    logger.debug(f'geotransform={geotransform}')
    started_at = datetime.now()
    logger.debug('reprojecting...')
    x_index, y_index = projection(lon_masked, lat_masked)
    logger.debug(f'reprojection done: {(datetime.now() - started_at).seconds}s')
    assert x_index.shape == y_index.shape, 'x_index.shape != y_index.shape'
    assert np.all(np.isfinite(x_index)), 'x_index contains non-finite numbers'
    assert np.all(np.isfinite(x_index)), 'y_index contains non-finite numbers'
    x_index, y_index = np.int_(x_index), np.int_(y_index)

    logger.info('ОБРАБОТКА ЗАВЕРШЕНА ' + geofile.name)
    return ProcessedGeolocFile(info=geofile, lat=lat, lon=lon, x_index=x_index, y_index=y_index,
                               lonlat_mask=lonlat_mask, geotransform=geotransform, projection=projection)


def hlf_process_band_file(geofile: GeofileInfo, geoloc_file: ProcessedGeolocFile) -> Optional[np.ndarray]:
    """
    Обрабатывает band-файл, на данный момент работает только с SDR I-band файлами.
    """
    _require_band_notimpl(geofile)

    if geofile.is_edr:
        raise NotImplementedError()
    f = gdal_open(geofile)
    if geofile.file_type in GeofileInfo.I_BAND_SDR:
        iband_dataset = 'Reflectance' if geofile.file_type in GeofileInfo.I_BAND_SDR__REFLECTANCE else 'BrightnessTemperature'
        sub = gdal_read_subdataset(f, iband_dataset)
        arr = sub.ReadAsArray()
        arr = arr[geoloc_file.lonlat_mask]

        x_index = geoloc_file.x_index
        y_index = geoloc_file.y_index

        assert x_index.shape == arr.shape, 'x_index.shape != arr.shape'
        assert y_index.shape == arr.shape, 'y_index.shape != arr.shape'

        x_index -= np.min(x_index)
        y_index -= np.min(y_index)
        image_shape = (np.max(y_index) + 1, np.max(x_index) + 1)

        '''
                arr, data_mask, offset = trim_data(arr, ret_mask=True, ret_offset=True)
                # arr = get_pass_data(arr) # ???
                x_idx_masked = geoloc_file.x_index[data_mask]
                x_idx_masked -= np.min(x_idx_masked)
                y_idx_masked = geoloc_file.y_index[data_mask]
                y_idx_masked -= np.min(y_idx_masked)
                image_shape = (y_idx_masked.max() + 1, x_idx_masked.max() + 1)
        '''

        image = np.zeros(image_shape, 'uint16') + ND_NA
        image[y_index, x_index] = arr
        del arr
        image = np.flip(image, 0)
        image = fill_nodata(image)
        image = np.float_(image)
        # Поменять nodata на nan, применить ReflectanceFactors
        mask = is_nodata(image)
        image[mask] = np.nan

        factors = 'ReflectanceFactors' if iband_dataset == 'Reflectance' else 'BrightnessTemperatureFactors'
        data = h5py_get_dataset(geofile.path, factors)
        if data is not None:
            mask = ~mask
            image[mask] *= data[0]
            image[mask] += data[1]
        else:
            logger.warning('Не удалось получить ' + factors)

        return image

    logger.warning('На данный момент поддерживаются только типы файлов: ' +
                   ', '.join(GeofileInfo.I_BAND_SDR__REFLECTANCE) + ' файл с типом ' + geofile.file_type +
                   ' проигнорирован')
    return None


def hlf_process_fileset(geoloc: GeofileInfo, band_files: List[GeofileInfo], scale=2000, band_types=None
                        ) -> Tuple[ProcessedGeolocFile, List[Tuple[np.ndarray, GeofileInfo, Point]]]:
    if band_types:
        band_files = list(filter(lambda bf: bf.file_type in band_types, band_files))
    if len(band_files) == 0:
        raise ValueError('Band-файлы не найдены')
    geoloc_file = hlf_process_geoloc_file(geoloc, scale)
    results = []

    required_width = -1
    required_height = -1

    for file in band_files:
        processed = hlf_process_band_file(file, geoloc_file)
        if processed is None:
            results.append(None)
            continue

        # TODO trim_data по горизонтали

        if TRIM:
            processed, _, offset = trim_data(processed, trim_value=np.isnan, ret_offset=True)
        else:
            offset = Point(0, 0)

        required_width = max(required_width, processed.shape[1] + offset.x)
        required_height = max(required_height, processed.shape[0] + offset.y)

        results.append((processed, file, offset))

    # Теперь нужно изменить размер каждого band'а, так чтобы он был минимальный, но одинаковый для всех band'ов
    if TRIM:
        for i in range(len(results)):
            if results[i] is None:
                continue
            processed, info, offset = results[i]
            processed = np.pad(processed, (
                (offset.y, required_height - offset.y - processed.shape[0]),
                (offset.x, required_width - offset.x - processed.shape[1])), constant_values=(np.nan,))
            results[i] = processed, info, offset

    return geoloc_file, results


# endregion


# region logging errors

def _require_file_type_notimpl(info: GeofileInfo, type_: str):
    if info.file_type != GIMGO:
        logger.error('Поддерживаются только файлы типа ' + type_)
        raise NotImplementedError('Поддерживаются только файлы типа ' + type_)


def _require_band_notimpl(info: GeofileInfo):
    if not info.is_band:
        logger.error('Поддерживаются только band-файлы')
        raise AssertionError('Поддерживаются только band-файлы')


# region repr helper functions


class _Repr:
    _access_repr: dict = None

    @classmethod
    def gdal_access(cls, mode):
        """
        Конвертирует значения gdal.GA_XXXX (GA_ReadOnly, GA_Update и т.д.) в строку
        :param mode:
        :return:
        """
        if cls._access_repr is None:
            from osgeo import gdalconst
            ga_keys = list(filter(lambda key: key.startswith('GA_'), gdalconst.__dict__.keys()))
            ga_values = list(map(lambda key: gdalconst.__dict__[key], ga_keys))
            cls._access_repr = {ga_values[i]: ga_keys[i] for i in range(len(ga_values))}
        name = cls._access_repr.get(mode)
        if name is None:
            return f'{mode}/UNKNOWN'
        else:
            return f'{mode}/{name}'


# endregion

# region tiff functions


def save_as_tiff(path: str, geoloc: ProcessedGeolocFile, bands: List[np.ndarray]):
    assert len(bands) != 0, 'bands list is empty!'
    driver = require_driver('GTiff')
    file: gdal.Dataset = driver.Create(path, bands[0].shape[1], bands[0].shape[0], len(bands), gdal.GDT_Float32)
    wkt = geoloc.projection.crs.to_wkt()
    logger.debug('SetProjection: ' + wkt)
    file.SetProjection(wkt)
    file.SetGeoTransform(geoloc.geotransform)
    for bi in range(len(bands)):
        file.GetRasterBand(bi + 1).WriteArray(bands[bi])

# endregion
