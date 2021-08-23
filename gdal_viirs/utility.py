import inspect
import re
from typing import Dict, Optional

import fiona.transform
import h5py

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
        data = data[t:data.shape[0] - b, l:data.shape[1] - r]
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
        data = data[:, t:data.shape[1] - b, l:data.shape[2] - r]
        transform = transform * Affine.translation(l, t)
        return transform, data


def get_intersection(x1: float, y1: float, w1: int, h1: int,
                     x2: float, y2: float, w2: int, h2: int,
                     scalex: float, scaley: float):
    """
    Функция принимает координаты точек начала двух растров, ширину и высоту растров и масштаб по X и Y растров,
    функция возвращает кортеж из двух элементов, каждый из которых - тоже кортеж, из 4 целых чисел вида
    (top, right, bottom, left) - отступы сверху, справа, снизу, слева, которые нужно сделать для каждого из двух растров,
    чтобы получить растр одинакового размера, покрывающий одну и ту же зону.

    Использование функции предполагает, что растры имеют одинаковый масштаб и вращение.

    :param x1: координата X первого растра
    :param y1: координата Y первого растра
    :param w1: ширина первого растра
    :param h1: высота первого растра
    :param x2: координата X второго растра
    :param y2: координата Y второго растра
    :param w2: ширина второго растра
    :param h2: высота второго растра
    :param scalex: масштаб по X
    :param scaley: масштаб по Y
    :return:
    """
    left1 = max(0.0, x2 // abs(scalex) - x1 // abs(scalex))
    left2 = max(0.0, x1 // abs(scalex) - x2 // abs(scalex))
    right1 = max(0.0, x1 // abs(scalex) + w1 - x2 // abs(scalex) - w2)
    right2 = max(0.0, x2 // abs(scalex) + w2 - x1 // abs(scalex) - w1)

    top1 = max(0.0, y1 // abs(scaley) + h1 - y2 // abs(scaley) - h2)
    top2 = max(0.0, y2 // abs(scaley) + h2 - y1 // abs(scaley) - h1)
    bottom1 = max(0.0, y2 // abs(scalex) - y1 // abs(scalex))
    bottom2 = max(0.0, y1 // abs(scalex) - y2 // abs(scalex))

    return (round(top1), round(right1), round(bottom1), round(left1)), (
        round(top2), round(right2), round(bottom2), round(left2))


def get_data_intersection(data1: np.ndarray,
                          data1_transform: Affine,
                          data2: np.ndarray,
                          data2_transform: Affine):
    if data1_transform.a != data2_transform.a or data1_transform.e != data2_transform.e:
        raise ValueError('вычисление пересечения невозможно для двух растров с разным масштабом')
    if data1_transform.b != data2_transform.b or data1_transform.d != data2_transform.d:
        raise ValueError('вычисление пересечения невозможно для двух растров с разным вращением')
    scalex, scaley = data1_transform.a, data1_transform.e
    return get_intersection(
        data1_transform.xoff, data1_transform.yoff, data1.shape[1], data1.shape[0],
        data2_transform.xoff, data2_transform.yoff, data2.shape[1], data2.shape[0],
        scalex, scaley
    )


def apply_xy_lim(data: np.ndarray, transform: Affine, xlim, ylim, fill_value=np.nan):
    xleft = int(max(0, (xlim[0] - transform.c) // transform.a))
    xright = int(max(0, (transform.c + data.shape[1] * transform.a - xlim[1]) // transform.a))
    ybottom = int(max(0, (ylim[0] - transform.f) // transform.e))
    ytop = int(max(0, (transform.f + data.shape[0] * transform.e - ylim[1]) // transform.a))
    if ytop != 0:
        data[:ytop, :] = fill_value
    if ybottom != 0:
        data[data.shape[0] - ybottom:, :] = fill_value
    if xleft != 0:
        data[:, :xleft] = fill_value
    if xright != 0:
        data[:, data.shape[1] - xright:] = fill_value

    return data


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

    data_intr, mask_intr = get_data_intersection(data, data_transform, mask, mask_transform)
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


def crop_intersection(data1: np.ndarray,
                      data1_transform: Affine,
                      data2: np.ndarray,
                      data2_transform: Affine):
    intersect1, intersect2 = get_data_intersection(data1, data1_transform, data2, data2_transform)
    data1 = data1[intersect1[0]:data1.shape[0] - intersect1[2], intersect1[3]:data1.shape[1] - intersect1[1]]
    data2 = data2[intersect2[0]:data2.shape[0] - intersect2[2], intersect2[3]:data2.shape[1] - intersect2[1]]
    if data1.shape != data2.shape:
        if data1.shape[0] > data2.shape[0]:
            data2 = np.pad(data2, ((0, data1.shape[0] - data2.shape[0]), (0, 0)))
        elif data1.shape[0] < data2.shape[0]:
            data1 = np.pad(data1, ((0, data2.shape[0] - data1.shape[0]), (0, 0)))

        if data1.shape[1] > data2.shape[1]:
            data2 = np.pad(data2, ((0, 0), (0, data1.shape[1] - data2.shape[1])))
        elif data1.shape[1] < data2.shape[0]:
            data1 = np.pad(data1, ((0, 0), (0, data2.shape[1] - data1.shape[1])))

    assert data1.shape == data2.shape

    scalex, scaley = data1_transform.a, data1_transform.e
    if scalex > 0:
        data1_transform *= Affine.translation(intersect1[3], 0)
        data2_transform *= Affine.translation(intersect2[3], 0)
    else:
        data1_transform *= Affine.translation(-intersect1[1], 0)
        data2_transform *= Affine.translation(-intersect2[1], 0)

    if scaley > 0:
        data1_transform *= Affine.translation(0, intersect1[2])
        data2_transform *= Affine.translation(0, intersect1[2])
    else:
        data1_transform *= Affine.translation(0, -intersect1[0])
        data2_transform *= Affine.translation(0, -intersect1[0])
    return data1, data1_transform, data2, data2_transform


def transform_point(src_crs, dst_crs, point):
    xs, ys = fiona.transform.transform(src_crs, dst_crs, [point[0]], [point[1]])
    return xs[0], ys[0]


def transform_points(src_crs, dst_crs, points):
    points = np.array(points)
    xs = points[:, 0]
    ys = points[:, 1]
    xs, ys = fiona.transform.transform(src_crs, dst_crs, xs, ys)
    return np.array(list(zip(xs, ys)))
