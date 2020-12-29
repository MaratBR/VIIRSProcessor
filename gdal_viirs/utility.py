import inspect
import re
from typing import Dict, Iterable

import h5py
import rasterio.warp
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


def get_intersection(x1, y1, w1, h1, x2, y2, w2, h2, scalex, scaley):
    left1 = max(0.0, x2  // abs(scalex) - x1  // abs(scalex))
    left2 = max(0.0, x1  // abs(scalex) - x2  // abs(scalex))
    right1 = max(0.0, x1 // abs(scalex) + w1 - x2 // abs(scalex) - w2)
    right2 = max(0.0, x2 // abs(scalex) + w2 - x1 // abs(scalex) - w1)

    top1 = max(0.0, y1 // abs(scaley) + h1 - y2 // abs(scaley) - h2)
    top2 = max(0.0, y2 // abs(scaley) + h2 - y1 // abs(scaley) - h1)
    bottom1 = max(0.0, y2 // abs(scalex) - y1 // abs(scalex))
    bottom2 = max(0.0, y1 // abs(scalex) - y2 // abs(scalex))

    return (round(top1), round(right1), round(bottom1), round(left1)), (round(top2), round(right2), round(bottom2), round(left2))


def apply_mask(data: np.ndarray,
               data_transform: Affine,
               mask: np.ndarray,
               mask_transform: Affine,
               nd_value):
    #  A----------B  нам необходимо найти ту область,
    #  |data      |  которую нужно обрезать по маске
    #  |          |
    #  Q     Z----|-----X
    #  |     |....|     |
    #  |     |....|     |
    #  D-----|----C     |
    #        |      mask|
    #        V----------Y
    if len(data.shape) not in (2, 3):
        raise ValueError('функция apply_mask работает только с 2-х и 3-х мерными массивами')
    if mask.dtype != np.bool_:
        raise ValueError('маска должна быть массивом из логических значений bool')
    if len(data.shape) == 2:
        shape = data.shape
    else:
        shape = data.shape[1:]

    if mask_transform.a != data_transform.a or mask_transform.e != data_transform.e:
        raise ValueError('применение маски невозможно для двух растров с разным масштабом')
    if mask_transform.b != data_transform.b or mask_transform.d != data_transform.d:
        raise ValueError('применение маски невозможно для двух растров с разным вращением')

    scalex, scaley = data_transform.a, data_transform.e
    data_intr, mask_intr = get_intersection(
        data_transform.xoff, data_transform.yoff, shape[1], shape[0],
        mask_transform.xoff, mask_transform.yoff, mask.shape[1], mask.shape[0],
        scalex, scaley
    )

    mask = mask[
        mask_intr[0]:mask.shape[0] - mask_intr[2],
        mask_intr[3]:mask.shape[1] - mask_intr[1]
    ]
    if len(data.shape) == 2:
        data[
            data_intr[0]:shape[0] - data_intr[2],
            data_intr[3]:shape[1] - data_intr[1]
        ][mask] = nd_value
    else:
        data[
            :,
            data_intr[0]:shape[0] - data_intr[2],
            data_intr[3]:shape[1] - data_intr[1]
        ][mask] = nd_value

    return data
