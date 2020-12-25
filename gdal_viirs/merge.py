import os
from datetime import datetime
from typing import List, Union, Tuple
import numpy as np
import rasterio
import rasterio.crs
from affine import Affine
from rasterio.merge import merge as _merge

import gdal_viirs.utility as _utility

MergeDataset = Union[rasterio.DatasetReader, str]


def merge_files(datasets: List[MergeDataset], **kw) -> Tuple[np.ndarray, rasterio.Affine, rasterio.crs.CRS]:
    open_datasets = []
    internally_open = []
    for ds in datasets:
        if isinstance(ds, str):
            f = rasterio.open(ds)
            internally_open.append(f)
            open_datasets.append(f)
        else:
            open_datasets.append(ds)
    try:
        if 'method' not in kw:
            kw['method'] = 'max'
        data, transform = _merge(open_datasets, **kw)
        top, right, bottom, left = _utility.get_trimming_offsets(data)
        data = data[top:data.shape[0] - bottom, left:data.shape[1] - right]
        transform *= Affine.translation(left * transform.a, top * transform.e)
        return data, transform, open_datasets[0].crs
    finally:
        for f in internally_open:
            f.close()


def merge_files2tiff(datasets: List[MergeDataset], out_dir: str, filename=None, **kw):
    merged, transform, crs = merge_files(datasets, **kw)
    filename = filename or datetime.now().strftime('merged_%Y_%m_%d_%H%M%S.tiff')
    filepath = os.path.join(out_dir, filename)
    meta = _utility.make_rasterio_meta(merged.shape[1], merged.shape[2], merged.shape[0])
    meta.update({
        'transform': transform,
        'crs': crs
    })
    with rasterio.open(filepath, 'w', **meta) as f:
        f.write(merged)
