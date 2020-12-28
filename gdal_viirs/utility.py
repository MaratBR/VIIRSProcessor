import inspect
import re
from typing import Dict, Iterable

import h5py
from affine import Affine

from gdal_viirs.types import *


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


def _find_viirs_files(root: str) -> List[GeofileInfo]:
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
                            prefer_parallax_corrected: Optional[bool] = False) -> Dict[str, ViirsFileset]:
    result = {}
    files = _find_viirs_files(root)
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
        result[fileinfo.name] = ViirsFileset(geoloc_file=fileinfo, band_files=band_files)
    return result


def get_filename(fileset: Union[ViirsFileset, ProcessedFileSet], type_='out'):
    return type_ + '_' + fileset.geoloc_file.name_without_extension + f'.tiff'


def get_trimming_offsets(data: np.ndarray, nodata=None):
    if not inspect.isfunction(nodata):
        if nodata is None:
            nodata_fn = np.isnan
        else:
            nodata_fn = lambda d: d == nodata
    else:
        nodata_fn = nodata

    nd_rows = np.all(nodata_fn(data), axis=0)
    nd_cols = np.all(nodata_fn(data), axis=1)
    left_off = nd_rows.argmin()
    right_off = nd_rows[::-1].argmin()
    top_off = nd_cols.argmin()
    bottom_off = nd_cols[::-1].argmin()
    return top_off, right_off, bottom_off, left_off


def make_rasterio_meta(height, width, bands_count, omit=None):
    meta = {
        'height': height,
        'width': width,
        'count': bands_count,
        'driver': 'GTiff',
        'nodata': np.nan,
        'dtype': 'float32'
    }
    if omit:
        for k in omit:
            del meta[k]
    return meta


def trim_nodata(data: np.ndarray,
                transform: Affine,
                nodata=None) -> Tuple[Optional[Affine], np.ndarray]:

    if len(data.shape) not in (2, 3):
        raise ValueError('неверная размерность массива, допускаются только 2-х и 3-х мерные массивы')
    if len(data.shape) == 2:
        # двух-мерный массив, просто обрезать и вернуть назад
        t, r, b, l = get_trimming_offsets(data, nodata)
        data = data[t:data.shape[0]-b, l:data.shape[1]-r]
        transform = transform * Affine.translation(l, t)
        return transform, data
    else:
        if data.shape[0] == 0:
            raise ValueError(f'размерность массива {data.shape} не поддерживается')
        # трех мерный массив, который является массивом из двухмерных
        # как следствие нужно вычислить минимальную область обрезки
        t, r, b, l = 1_000_000_000, 1_000_000_000, 1_000_000_000, 1_000_000_000
        for processed_band in data:
            t2, r2, b2, l2 = get_trimming_offsets(processed_band, nodata)
            t, r, b, l = min(t, t2), min(r, r2), min(b, b2), min(l, l2)
        data = data[:, t:data.shape[1]-b, l:data.shape[2]-r]
        transform = transform * Affine.translation(l, t)
        return transform, data
