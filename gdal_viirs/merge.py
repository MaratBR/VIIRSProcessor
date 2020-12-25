import os
from typing import List, Union, Tuple
import numpy as np
import rasterio
from rasterio.merge import merge as _merge

from gdal_viirs import utility

MergeDataset = Union[rasterio.DatasetReader, str]


def merge_files(datasets: List[MergeDataset], **kw) -> Tuple[np.ndarray, rasterio.Affine]:
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
        return _merge(open_datasets, **kw)
    finally:
        for f in internally_open:
            f.close()


def merge_files2tiff(datasets: List[MergeDataset], out_dir: str, filename=None, **kw):
    merged, transform = merge_files(datasets, **kw)
    filepath = os.path.join(out_dir, filename)
    meta = utility.make_rasterio_meta(merged.shape[1], merged.shape[2], merged.shape[0])
    meta.update({
        'transform': transform
    })
    with rasterio.open(filepath, 'w', **meta, **meta) as f:
        f.write(merged)
