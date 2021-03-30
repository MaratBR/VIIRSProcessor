import numpy as np
from matplotlib import patches
from matplotlib.colors import ListedColormap, BoundaryNorm

from gdal_viirs.maps.rcpod import RCPODMapBuilder


def _split_degree(deg):
    degree = int(deg)
    deg -= degree
    deg *= 60
    minutes = int(deg)
    deg -= minutes
    deg *= 60
    seconds = int(deg)
    return degree, minutes, seconds


NDVI_BAD = '#c0504d'
NDVI_OK = '#ffff00'
NDVI_GOOD = '#70a800'
NDVI_CLOUD = '#8c8c8c'


class NDVIMapBuilder(RCPODMapBuilder):
    bottom_title = 'Мониторинг состояния посевов зерновых культур'

    def init(self):
        self.cmap = ListedColormap(['#aaa', "red", "yellow", 'greenyellow'])
        self.norm = BoundaryNorm([-2, -1, .4, .7], 4)

    def get_legend_handles(self):
        data = self.file.read(1)
        data_mask = ~np.isnan(data)
        all_count = max(1, np.count_nonzero(data_mask))
        bad_count = np.count_nonzero(data_mask * (data < 0.3) * (data >= -1))
        ok_count = np.count_nonzero(data_mask * (data < 0.7) * (data >= 0.3))
        good_count = np.count_nonzero(data_mask * (data >= 0.7))
        clouds_count = np.count_nonzero(data == -2)
        del data

        return [
            patches.Patch(color=NDVI_BAD, label=f'Плохое ({round(1000 * bad_count / all_count) / 10}%)'),
            patches.Patch(color=NDVI_OK, label=f'Удовлетворительное ({round(1000 * ok_count / all_count) / 10}%)'),
            patches.Patch(color=NDVI_GOOD, label=f'Хорошее ({round(1000 * good_count / all_count) / 10}%)'),
            patches.Patch(color=NDVI_CLOUD,
                          label=f'Закрытые облачностью посевы ({round(1000 * clouds_count / all_count) / 10}%)'),
        ]
