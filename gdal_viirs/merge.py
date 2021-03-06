from typing import List, Union, Tuple

import numpy as np
import rasterio
import rasterio.crs
from rasterio.merge import merge as _merge

import gdal_viirs.utility as _utility

MergeDataset = Union[rasterio.DatasetReader, str]


def merge_files(datasets: List[str], **kw) -> Tuple[np.ndarray, rasterio.Affine, rasterio.crs.CRS]:
    open_datasets = []
    for ds in datasets:
        f = rasterio.open(ds)
        open_datasets.append(f)
    try:
        if 'method' not in kw:
            kw['method'] = 'max'
        data, transform = _merge(open_datasets, **kw)
        transform, data = _utility.trim_nodata(data, transform)
        return data, transform, open_datasets[0].crs
    finally:
        for f in open_datasets:
            f.close()


def merge_files2tiff(datasets: List[MergeDataset], output_file: str, **kw):
    merged, transform, crs = merge_files(datasets, **kw)
    meta = _utility.make_rasterio_meta(merged.shape[1], merged.shape[2], merged.shape[0])
    meta.update({
        'transform': transform,
        'crs': crs
    })
    with rasterio.open(output_file, 'w', **meta) as f:
        f.write(merged)
