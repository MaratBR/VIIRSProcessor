import os
import re
from typing import List, Dict, Optional, Union

import h5py

from gdal_viirs.exceptions import *
from gdal_viirs.types import *


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


def h5py_get_dataset(filename: str, dataset_lastname: str) -> Optional[h5py.File]:
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
    try:
        files = os.listdir(root)
    except FileNotFoundError:
        return []
    regex = re.compile(r"^[a-zA-Z0-9]+_[a-zA-Z0-9]+_d\d+_t\d+_e\d+_b\d+_c\d+_\w+\.h5$")
    files = filter(lambda filename: regex.match(filename) is not None, files)
    files = map(lambda p: os.path.join(root, p), files)
    files = list(map(GeofileInfo, files))

    return files


def find_sdr_viirs_filesets(root,
                            geoloc_types: Optional[List[str]] = None,
                            prefer_parallax_corrected: Optional[bool] = False) -> Dict[str, ViirsFileSet]:
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


def get_filename(fileset: Union[ViirsFileSet, ProcessedFileSet], type_='out'):
    return type_ + '_' + fileset.geoloc_file.name_without_extension + f'.tiff'