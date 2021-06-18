import numpy as np
from matplotlib import patches
from matplotlib.colors import ListedColormap, BoundaryNorm

from gdal_viirs.maps.rcpod import RCPODMapBuilder


class NDVIDynamicsMapBuilder(RCPODMapBuilder):
    bottom_title = 'Динамика развития посевов'

    def init(self):
        self.cmap = ListedColormap(['#8c8c8c', "#a11f14", "#ffaa00", '#ffff00', '#98e600', '#3b7a17'])
        self.norm = BoundaryNorm([-999, -998.999, -45, -15, 15, 45, 999], 6)

    def get_legend_handles(self):
        data = self.read_data()
        data_mask = ~np.isnan(data)
        all_count = max(1, np.count_nonzero(data_mask))
        clouds_count = np.count_nonzero((data <= -999) * data_mask)
        sign_degr_count = np.count_nonzero(data_mask * (data < -45) * (data > -999))
        degr_count = np.count_nonzero(data_mask * (data >= -45) * (data < -15))
        min_change_count = np.count_nonzero(data_mask * (data >= -15) * (data < 15))
        impr_count = np.count_nonzero(data_mask * (data >= 15) * (data < 45))
        sign_impr_count = np.count_nonzero(data_mask * (data >= 45))
        del data

        return [
            patches.Patch(color='#3b7a17',
                          label=f'Значительное улучшение >45%  ({round(10000 * sign_impr_count / all_count) / 100}%)'),
            patches.Patch(color='#98e600',
                          label=f'Улучшение 15 - 45% ({round(10000 * impr_count / all_count) / 100}%)'),
            patches.Patch(color='#ffff00',
                          label=f'Незначительное изменение (-15) - 15% ({round(10000 * min_change_count / all_count) / 100}%)'),
            patches.Patch(color='#ffaa00',
                          label=f'Ухудшение (-45) - (-15)%  ({round(10000 * degr_count / all_count) / 100}%)'),
            patches.Patch(color='#a11f14',
                          label=f'Значительное ухудшение <(-45)% ({round(10000 * sign_degr_count / all_count) / 100}%)'),
            patches.Patch(color='#8c8c8c',
                          label=f'Закрытые облачностью посевы ({round(10000 * clouds_count / all_count) / 100}%)'),
        ]
