import os

import gdal
import uuid

from gdal_viirs.v2 import require_driver
from gdal_viirs.v2.exceptions import InvalidData

_cache_dir = '/tmp'
_prefer_fs = False
generated_files = []


def set_directory(directory):
    global _cache_dir
    _cache_dir = directory


def set_prefer_fs(v: bool):
    global _prefer_fs
    _prefer_fs = v


def _generate_filename():
    name = f'gdal-viirs_pid{os.getpid()}_{uuid.uuid4().hex}.tiff'
    generated_files.append(os.path.join(_cache_dir, name))
    return name


def clear_cache():
    for filename in generated_files:
        try:
            os.remove(filename)
        except:
            # TODO log warning
            pass


def create(xsize, ysize, *, dtype=gdal.GDT_Float64, bands=1, use_memory=False, data: list=None) -> gdal.Dataset:
    use_memory = use_memory or not _prefer_fs
    if not use_memory:
        ds = require_driver('GTiff').Create(
            os.path.join(_cache_dir, _generate_filename()),
            xsize, ysize, bands)
    else:
        ds = require_driver('MEM').Create('', int(xsize), int(ysize), bands, eType=dtype)

    if data:
        if len(data) > bands:
            raise InvalidData(f'Передано больше растеров, чем выделено ({bands} выделено, {len(data)} передано)')

        for index, d in enumerate(data):
            ds.GetRasterBand(index + 1).WriteArray(d)

    return ds
