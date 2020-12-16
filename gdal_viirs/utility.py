import os
import re
import gdal
import h5py
from typing import List, Dict, Optional

from gdal_viirs.exceptions import DatasetNotFoundException, SubDatasetNotFound, InvalidData, GDALNonZeroReturnCode, \
    DriverNotFound
from gdal_viirs.types import DatasetLike, ViirsFileSet, GeofileInfo


def check_gdal_return_code(code):
    if code != 0:
        msg = gdal.GetLastErrorMsg()
        raise GDALNonZeroReturnCode(code, msg)


def require_driver(name: str) -> gdal.Driver:
    """
    Возвращается драйвер, выбрасывает
    :param name:
    :return:
    """
    driver = gdal.GetDriverByName(name)
    if driver is None:
        raise DriverNotFound(name)
    return driver


def create_mem(xsize, ysize, *, dtype=gdal.GDT_Float64, bands=1, data: list = None) -> gdal.Dataset:
    """
    Создает пустой датасет в памяти
    :param xsize: ширина
    :param ysize: высота
    :param dtype: тип данныз (gdal.GDT_Byte, gdal.GDT_Float64 и т. д.), по умолчанию - gdal.GDT_Float64
    :param bands: кол-во каналов (по-умолчанию - 1)
    :param data: данные в виде списка numpy массивов, размер списка не больше зачение bands
    :return: gdal.Dataset
    """
    ds = require_driver('MEM').Create('', int(xsize), int(ysize), bands, eType=dtype)

    if data:
        if len(data) > bands:
            raise InvalidData(f'Передано больше растеров, чем выделено ({bands} выделено, {len(data)} передано)')

        for index, d in enumerate(data):
            code = ds.GetRasterBand(index + 1).WriteArray(d)
            check_gdal_return_code(code)

    return ds


def get_lat_long_data(file: DatasetLike, ret_file: bool = True):
    """
    Открывает датасеты широты и долготы.

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
    return f


def gdal_read_subdataset(file: gdal.Dataset, dataset_lastname: str, mode=gdal.GA_ReadOnly,
                         exact_lastname=True) -> gdal.Dataset:
    """
    Прочитывает датасет из другого, родительского, датасета
    :return:
    """
    try:
        name = next(sub[0] for sub in file.GetSubDatasets() if
                    isinstance(sub[0], str) and sub[0].endswith(('/' if exact_lastname else '') + dataset_lastname))
    except StopIteration:
        raise SubDatasetNotFound(dataset_lastname)
    file = gdal_open(name, mode)
    return file


def h5py_get_dataset(filename: str, dataset_lastname: str) -> h5py.File:
    f = h5py.File(filename, 'r')
    datasets = []
    f.visit(datasets.append)
    try:
        ds = next(ds for ds in datasets if ds == dataset_lastname or ds.endswith('/' + dataset_lastname))
        data = f[ds][()]
        return data
    except StopIteration:
        return None


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


def find_sdr_viirs_filesets(root,
                            geoloc_types: Optional[List[str]] = None,
                            prefer_parallax_corrected: Optional[bool] = False) -> Dict[str, ViirsFileSet]:
    """
    Возвращает dictionary где ключами являются названия файлов геолокации (с широтой и долготой),
    а занчение - кортеж из двух элемFентов, первый - информация о файле геолокации, второй - список band-файлов
    """
    result = {}
    files = find_viirs_files(root)
    geoloc_types = geoloc_types or GeofileInfo.GEOLOC_SDR
    if prefer_parallax_corrected is not None:
        if prefer_parallax_corrected:
            geoloc_types = filter(lambda t: t not in GeofileInfo.GEOLOC_SMOOTH_ELLIPSOID, geoloc_types)
        else:
            geoloc_types = filter(lambda t: t not in GeofileInfo.GEOLOC_PARALLAX_CORRECTED, geoloc_types)
        geoloc_types = list(geoloc_types)
    geoloc_files = list(filter(lambda info: info.file_type in geoloc_types, files))
    for fileinfo in geoloc_files:
        band_file_types = fileinfo.get_band_files_types()
        band_files = list(filter(
            lambda info:
            info.file_type in band_file_types and
            info.t_start == fileinfo.t_start and
            info.t_end == fileinfo.t_end and
            info.orbit_number == fileinfo.orbit_number,
            files))
        band_files = sorted(band_files, key=lambda f: f.file_type)
        result[fileinfo.name] = ViirsFileSet(geoloc_file=fileinfo, band_files=band_files)
    return result
