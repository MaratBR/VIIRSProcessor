import math
import warnings

import cartopy
import rasterio.plot
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from rasterio import DatasetReader
from matplotlib import rcParams, patches, lines

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Times', 'Times New Roman', 'Serif']

from gdal_viirs.maps import _drawings
from gdal_viirs.maps.builder import MapBuilder, cm


class NDVIMapBuilder(MapBuilder):
    def __init__(self):
        super(NDVIMapBuilder, self).__init__()
        self.xlim = -1500000, 2100000
        self.ylim = 800000, 3000000
        self.add_point(84.948197, 56.484680, 'Томск')
        self.add_point(73.368212, 54.989342, 'Омск')
        self.add_point(86.087314, 55.354968, 'Кемерово')
        self.add_point(82.933952, 55.018803, 'Новосибирск')
        self.margin = cm(1)
        self.cmap = ListedColormap(['#aaa', "red", "yellow", 'greenyellow'])
        self.norm = BoundaryNorm([-999, -1, .4, .7], 3)
        self.outer_size = cm(6), self.margin, cm(7), self.margin + cm(12)
        self.map_mark_min_length = cm(1)
        self.map_mark_thickness = cm(.25)
        self.map_mark_dist = 1, 1, 2, 2, 3
        self.map_mark_colors = 'black', 'white'

    def plot(self, file: DatasetReader, band=1):
        fig, (ax0, ax1), size = super(NDVIMapBuilder, self).plot(file, band)
        top_gap = self.outer_size[0]
        logo_size = top_gap * .75
        logo_padding = top_gap * .0375
        _drawings.draw_image('./logo.png', (self.margin + logo_padding, logo_padding + cm(.5)), ax0,
                             max_width=logo_size, max_height=logo_size,
                             origin=_drawings.TOP_LEFT)

        text_left = self.margin + logo_size + logo_padding*2 + cm(.75)
        _drawings.draw_text('ФГБУ «НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ЦЕНТР КОСМИЧЕСКОЙ ГИДРОМЕТЕОРОЛОГИИ «ПЛАНЕТА»\nСИБИРСКИЙ ЦЕНТР',
                            (text_left, cm(1.5)), ax0,
                            wrap=True, fontsize=26, va='top', ha='left', invert_y=True)
        _drawings.draw_text('\n'.join([
            'Сибирский центр',
            'ФГБУ НИЦ «ПЛАНЕТА»',
            'Россия, 630099, г. Новосибирск',
            'ул. Советская, 30',
            'Тел. (383) 363-46-05',
            'Факс. (383) 363-46-05',
            'E-mail: kav@rcpod.siberia.net',
            'http://rcpod.ru'
        ]), (self.margin, self.margin), ax0, fontsize=15, va='bottom', ha='left')
        _drawings.draw_text('Мониторинг состояния посевов зерновых культур', (fig.get_size_inches()[0] / 2, self.outer_size[2] / 2), ax0,
                            ha='center', va='top', fontsize=25, weight='bold')
        #self._draw_histogram(fig, file, size, band)
        self._draw_legend(ax0)
        self._draw_map_marks(ax0, file, size)

        return fig, (ax0, ax1), size

    def get_projection(self, file):
        return cartopy.crs.LambertConformal(standard_parallels=(67.41206675, 43.58046825), central_longitude=79.950619)

    def _draw_histogram(self, fig, file, size, band):
        w, h = self.outer_size[1] - self.margin - cm(2), min(cm(30), size[1] / 2)
        pos = self.outer_size[1] - cm(2) - w, self.outer_size[0]
        ax = _drawings.get_axes_area(fig, pos, w, h, origin=_drawings.TOP_RIGHT)
        data = file.read(band).copy()
        data[data < -1] = np.nan
        rasterio.plot.show_hist(data, ax=ax, bins=100, lw=0.0, title='Распределение',
                                histtype='stepfilled', stacked=False, alpha=1, label='NDVI')

    def _draw_legend(self, ax0):
        # ----
        # Условные обозначения
        # ----
        top = self.outer_size[0] + self.margin
        _drawings.draw_text('Suomi NPP/VIIRS', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', weight='bold', fontsize=23, invert_y=True)
        top += self.margin * 2
        _drawings.draw_text('Состояние посевов', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', fontsize=20, invert_y=True)
        top += cm(6)
        loc = _drawings.inches2axes(ax0, (self.margin, top))
        loc = loc[0], 1 - loc[1]
        leg1 = ax0.legend(handles=[
            patches.Patch(color='red', label='Плохое'),
            patches.Patch(color='yellow', label='Удовлетворительное'),
            patches.Patch(color='greenyellow', label='Хорошое'),
            patches.Patch(color='#aaa', label='Закрыто облаками'),
        ], loc=loc, edgecolor='none', fontsize=20)

        top += cm(1)

        _drawings.draw_text('Условные обозначения', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', fontsize=20, invert_y=True)

        top += cm(6)
        loc = _drawings.inches2axes(ax0, (self.margin, top))
        loc = loc[0], 1 - loc[1]
        ax0.legend(handles=[
            lines.Line2D([], [], linewidth=2, color='k', linestyle=':', label='Границы субъектов'),
            lines.Line2D([], [], linewidth=4, color='k', label='Границы стран'),
            lines.Line2D([], [], color="none", marker='o', markersize=20, markerfacecolor="blue",
                         label='Населенные пункты'),
            patches.Patch(color='blue', label='Водоёмы'),
        ], loc=loc, edgecolor='none', fontsize=20)
        ax0.add_artist(leg1)

    def _draw_map_marks(self, ax0, file: DatasetReader, size):
        transform = file.transform

        pixels_per_km_x = 1000 / transform.a
        inches_per_km_x = pixels_per_km_x / ax0.figure.dpi
        km_per_segment = math.floor(self.map_mark_min_length / inches_per_km_x)
        if km_per_segment > 30 and km_per_segment % 10 != 0:
            km_per_segment = round(km_per_segment / 10) * 10
        inches_per_segment = km_per_segment * inches_per_km_x

        left = self.outer_size[3]
        odd = True
        km = 0
        y = self.outer_size[2] - self.margin - self.map_mark_thickness
        for dist in self.map_mark_dist:
            km += km_per_segment * dist
            w_inches = dist * inches_per_segment
            w, h = _drawings.inches2axes(ax0, (w_inches, self.map_mark_thickness))
            xy = _drawings.inches2axes(ax0, (left, y))
            color = self.map_mark_colors[0] if odd else self.map_mark_colors[1]
            rect1 = patches.Rectangle(xy, color=color, width=w, height=h)
            ax0.add_artist(rect1)
            _drawings.draw_text(str(km), (left + w_inches, y - h - cm(.1)), ax0, va='top', ha='right')
            left += w_inches
            odd = not odd

        _drawings.draw_rect_with_outside_border((self.outer_size[3], y),
                                                sum(self.map_mark_dist) * inches_per_segment,
                                                self.map_mark_thickness, ax0)


