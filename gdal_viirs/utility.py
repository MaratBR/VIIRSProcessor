import re
from typing import Dict, Iterable

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


def get_trimming_offsets(data: np.ndarray, nodata=np.isnan):
    nd_rows = np.all(nodata(data), axis=0)
    nd_cols = np.all(nodata(data), axis=1)
    left_off = nd_rows.argmin()
    right_off = nd_rows[::-1].argmin()
    top_off = nd_cols.argmin()
    bottom_off = nd_cols[::-1].argmin()
    return top_off, right_off, bottom_off, left_off


def make_rasterio_meta(height, width, bands_count):
    return {
        'height': height,
        'width': width,
        'count': bands_count,
        'driver': 'GTiff',
        'nodata': np.nan,
        'dtype': 'float32'
    }


def trim_nodata(bands_in: Iterable[ProcessedBandFile], geotransform: GDALGeotransformT, scale: Number) -> Tuple[GDALGeotransformT, List[ProcessedBandFile]]:
    bands = []
    top, right, bottom, left = [1_000_000_000] * 4
    for processed_band in bands_in:
        top2, right2, bottom2, left2 = get_trimming_offsets(processed_band.data)
        top, right, bottom, left = min(top, top2), min(right, right2), min(bottom, bottom2), min(left, left2)
        bands.append(processed_band)

    if top > 0 or right > 0 or bottom > 0 or left > 0:
        for i in range(len(bands)):
            band = bands[i]
            data = band.data[top:band.data.shape[0] - bottom, left:band.data.shape[1] - right]
            bands[i] = ProcessedBandFile(
                data=data,
                geoloc_file=band.geoloc_file
            )
        assert len(set(band.data.shape for band in bands)) == 1, 'не все массивы имеют одинаковый размер'
        geotransform = (
            geotransform[0] + left * scale,
            geotransform[1],
            geotransform[2],
            geotransform[3] - top * scale,
            geotransform[4],
            geotransform[5]
        )
        return geotransform, bands
