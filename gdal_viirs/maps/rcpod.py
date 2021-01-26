import math
import cartopy
import numpy as np

from matplotlib.colors import ListedColormap, BoundaryNorm
from rasterio import DatasetReader
from matplotlib import patches, lines

from gdal_viirs import utility
from gdal_viirs.hl import points

from gdal_viirs.maps import _drawings
from gdal_viirs.maps.builder import MapBuilder, cm


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
STATES_BORDER_COLOR = '#a80000'
REGIONS_BORDER_COLOR = '#9c9c9c'
NDVI_CLOUD = '#8c8c8c'


class RCPODMapBuilder(MapBuilder):
    bottom_title = ''
    bottom_subtitle = None
    date_text = None

    def __init__(self, logo_path='./logo.png', map_points=None, iso_sign_path=None, **kwargs):
        super(RCPODMapBuilder, self).__init__(**kwargs)
        self.styles.update({
            'regions_border': REGIONS_BORDER_COLOR,
            'states_border': STATES_BORDER_COLOR,
            'ndvi_ok': NDVI_OK,
            'ndvi_good': NDVI_GOOD,
            'ndvi_bad': NDVI_BAD,
            'ndvi_cloud': NDVI_CLOUD
        })
        points.add_points(self, [
            *points.SIBERIA_CITIES,
            *(map_points or []),
        ])
        self.margin = cm(1)
        self.cmap = ListedColormap(['#aaa', "red", "yellow", 'greenyellow'])
        self.norm = BoundaryNorm([-2, -1, .4, .7], 4)
        self.outer_size = cm(10), self.margin, cm(8.5), self.margin + cm(14)
        self.min_height = cm(30)
        self.logo_path = logo_path
        self.iso_sign_path = iso_sign_path

        # настройка параметров для меток на карте
        self.map_mark_min_length = cm(1)  # минимальная длина сегмента обозначения длинны
        self.map_mark_thickness = cm(.25)  # толщина сегмента
        self.map_mark_dist = 1, 1, 2, 2, 3  # длинная сегментов, измеренная в процентах по сравнению с минимальной
        self.map_mark_colors = 'black', 'white'  # чередующиеся цвета сегментов

        self.map_mark_degree_seg_len = cm(5)  # минимальное растояние между отметками градусов на карте
        self.map_latlong_mark_thickness = cm(.1)  # толщина отметок
        self.map_latlon_mark_len = cm(.35)  # длинна отметок

        self.init()

    def init(self):
        pass

    def get_legend_handles(self, file: DatasetReader):
        return []

    def plot(self, file: DatasetReader, band=1):
        fig, (ax0, ax1), size = super(RCPODMapBuilder, self).plot(file, band)
        logo_size = cm(3)  # размер лого - 75% от толщины верхней зоны
        logo_padding = cm(.7)  #

        # рисуем логотип в верхнем левом углу
        _drawings.draw_image(self.logo_path, (self.margin + logo_padding, logo_padding + cm(.5)), ax0,
                             max_width=logo_size, max_height=logo_size,
                             origin=_drawings.TOP_LEFT)
        _drawings.draw_image(self.iso_sign_path, (self.margin, self.margin), ax0,
                             max_width=cm(2), max_height=cm(2),
                             origin=_drawings.BOTTOM_RIGHT)

        title_width = fig.get_size_inches()[0] - self.margin * 2 - logo_padding - logo_size
        _drawings.draw_text('ФЕДЕРАЛЬНАЯ СЛУЖБА ПО ГИДРОМЕТЕОРОЛОГИИ И МОНИТОРИНГУ ОКРУЖАЮЩЕЙ СРЕДЫ\n'
                            'ФГБУ "НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ЦЕНТР КОСМИЧЕСКОЙ МЕТЕОРОЛОГИИ "ПЛАНЕТА"\n'
                            'СИБИРСКИЙ ЦЕНТР',
                            (self.margin * 2 + logo_padding + logo_size + title_width / 2,
                             self.outer_size[0] / 2), ax0,
                            max_size=(title_width, self.outer_size[0]),
                            wrap=True, fontproperties=self._get_font_props(size=30),
                            va='center', ha='center', origin=_drawings.TOP_LEFT)
        _drawings.draw_text('\n'.join([
            'Сибирский центр',
            'ФГБУ НИЦ «ПЛАНЕТА»',
            'Россия, 630099, г. Новосибирск',
            'ул. Советская, 30',
            'Тел. (383) 363-46-05',
            'Факс. (383) 363-46-05',
            'E-mail: kav@rcpod.siberia.net',
            'http://rcpod.ru'
        ]), (self.margin, self.margin), ax0, fontproperties=self._get_font_props(size=18), va='bottom', ha='left')

        _drawings.draw_text(self.bottom_title + '\n' + (self.bottom_subtitle or ''),
                            (self.outer_size[3] + size[0] / 2, self.margin), ax0, max_size=(size[0], cm(3.5)),
                            ha='center', va='bottom', fontproperties=self._get_font_props(size=36))

        if self.date_text:
            _drawings.draw_text(self.date_text,
                                (fig.get_size_inches()[0] - self.outer_size[1], self.margin * 1.3 + cm(3.5)),
                                ax0, ha='right', va='bottom',
                                fontproperties=self._get_font_props(size=26))

        self._draw_legend(ax0, file)
        self._draw_map_marks(ax0, file)
        self._draw_scale_line(file, ax0)

        return fig, (ax0, ax1), size

    def get_projection(self, file):
        return cartopy.crs.LambertConformal(
            standard_parallels=(67.41206675, 43.58046825),
            central_longitude=80,
            central_latitude=55.4962675
        )

    def _draw_legend(self, ax0, file):
        """
        Рисуем легенду для изображенния и некоторый текст
        """
        top = self.outer_size[0] + self.margin  # отступ сверху

        l = _drawings.LinearLayout(ax0, (self.outer_size[3] / 2, top), origin=_drawings.TOP_LEFT)
        l.set_spacing(cm(.6))
        l.text('КА Suomi NPP/VIIRS', fontproperties=self._get_font_props(size=28))
        l.text('Разрешение 375 м', fontproperties=self._get_font_props(size=22))
        l.spacing(cm(.9))
        l.text('Условные обозначения', fontproperties=self._get_font_props(size=26))
        l.spacing(cm(.4))
        l.legend(handles=[
            lines.Line2D([], [], linewidth=2, color='#666666', label='Границы районов'),
            lines.Line2D([], [], linewidth=4, color='k', label='Границы субъектов'),
            lines.Line2D([], [], marker='o', markersize=20, markerfacecolor='white', color='none',
                         markeredgecolor='k', linewidth=2, label='Населенные пункты'),
            patches.Patch(color='blue', label='Водоёмы'),
        ], edgecolor='none', prop=self._get_font_props(size=20))
        l.text('Состояние посевов', fontproperties=self._get_font_props(size=22))
        l.legend(handles=self.get_legend_handles(file), edgecolor='none', prop=self._get_font_props(size=20))

    def _get_pixels_per_km(self, file: DatasetReader):
        pixels_per_km_x = 1000 / file.transform.a
        xlim = self._get_lims(file)[0]
        zoom = abs(xlim[0] - xlim[1]) / (file.transform.a * file.width)
        pixels_per_km_x /= zoom
        return pixels_per_km_x

    def _draw_scale_line(self, file: DatasetReader, ax):
        fontprops = self._get_font_props(size=16)
        # расчитываем, сколько дюймов должно приходится на один сегмент
        pixels_per_km_x = self._get_pixels_per_km(file)
        inches_per_km_x = pixels_per_km_x / ax.figure.dpi
        km_per_segment = math.floor(self.map_mark_min_length / inches_per_km_x)
        if km_per_segment > 30 and km_per_segment % 10 != 0:
            km_per_segment = round(km_per_segment / 10) * 10
        inches_per_segment = km_per_segment * inches_per_km_x

        y = self.outer_size[2] - self.margin * 1.5 - self.map_mark_thickness
        km_width = _drawings.draw_text('км', (self.outer_size[1], y + self.map_mark_thickness / 2), ax,
                                       origin=_drawings.BOTTOM_RIGHT, fontproperties=fontprops,
                                       align=_drawings.Alignment(hor=_drawings.RIGHT, ver=_drawings.VCENTER))[0]

        left_offset = left = self.outer_size[3] + self._get_raster_size_inches(file)[0] - inches_per_segment * sum(
            self.map_mark_dist) - km_width - cm(.2)
        odd = True
        km = 0

        # рисуем отметки по указанным значениям распределения
        # Напремер, если self.map_mark_dist = (1, 2, 3, 2, 5), это значит, что будет 5
        # отметок, первая будет иметь длинну 100%, вторая 200% и т. д.
        for dist in self.map_mark_dist:
            km += km_per_segment * dist
            w_inches = dist * inches_per_segment
            w, h = _drawings.inches2axes(ax, (w_inches, self.map_mark_thickness))
            xy = _drawings.inches2axes(ax, (left, y))
            color = self.map_mark_colors[0] if odd else self.map_mark_colors[1]
            rect1 = patches.Rectangle(xy, color=color, width=w, height=h)
            ax.add_artist(rect1)
            _drawings.draw_text(str(km), (left + w_inches, y - h - cm(.1)), ax, va='top', ha='right',
                                fontproperties=fontprops)
            left += w_inches
            odd = not odd

        # рисуем окантовку
        # TODO цвет окантовки
        _drawings.draw_rect_with_outside_border(ax, (left_offset, y),
                                                sum(self.map_mark_dist) * inches_per_segment,
                                                self.map_mark_thickness)

    def _draw_map_marks(self, ax0, file: DatasetReader):
        """
        Рисует пометки на карте, это включает в себя:
            * отметка, обозначающая масштаб в виде "линейки"
            * отметки о градусах широты/долготы на карте
        Использование данной функции предпологает, что масштабы по осям X и Y одинаковы
        :param ax0:  объект типа Axes, используемы для рисования и покрывающий весь рисунок
        :param file: открытый файл rasterio
        :return:
        """

        # отметки в грудусах
        transform = file.transform
        fontprops = self._get_font_props(size=16)
        src_crs = file.crs.to_proj4()
        xlim, ylim = self._get_lims(file)
        bl_xy, br_xy, tl_xy, tr_xy = (
            (xlim[0], ylim[0]),
            (xlim[1], ylim[0]),
            (xlim[0], ylim[1]),
            (xlim[1], ylim[1])
        )
        pts = utility.transform_points(src_crs, 'EPSG:4326', (bl_xy, br_xy, tl_xy, tr_xy))
        bl, br, tl, tr = pts
        del pts

        plot_w, plot_h = ax0.figure.get_size_inches()
        raster_w = plot_w - self.outer_size[1] - self.outer_size[3]
        raster_h = plot_h - self.outer_size[2] - self.outer_size[0]
        xy_per_inch = abs(xlim[0] - xlim[1]) / raster_w

        # для каждой линии мы вычисляем точку откуда нужно начинать рисовать отметки после чего вычисляем
        # координаты этой точкий в проекции, далее к X или Y данной точки начинаем прибовалять значение, высчитанное
        # заранее, таким образом вычисляются координаты каждой точки для каждой линии
        # количество точек в линии вычисляется на основании минимальной длинны между точками и длинне/высоте растра

        # верхняя линия
        inches_per_lon_deg_top = raster_w / (tr[0] - tl[0])
        degrees_per_segment_top = math.ceil(self.map_mark_degree_seg_len / inches_per_lon_deg_top * 3600) / 3600
        segment_top_size = min(degrees_per_segment_top * inches_per_lon_deg_top, raster_w / 2)
        segments_count_top = int(raster_w // segment_top_size)

        # начинаем рисовать верхнюю линию
        top = self.outer_size[0]
        offset_x = (raster_w - (segments_count_top - 1) * segment_top_size) / 2
        left = self.outer_size[3] + offset_x
        left_xy = tl_xy[0] + xy_per_inch * offset_x
        del offset_x

        for i in range(segments_count_top):
            w, h = self.map_latlong_mark_thickness, self.map_latlon_mark_len
            long, lat = utility.transform_point(src_crs, 'EPSG:4326', (left_xy, transform.f))
            degree, minutes, seconds = _split_degree(long)
            _drawings.draw_text(f'{degree}°{minutes}\'{seconds}\'\'', (left + cm(.05), plot_h - top + h + cm(.05)), ax0,
                                va='bottom', ha='center', fontsize=14, fontproperties=fontprops)

            xy = _drawings.inches2axes(ax0, (left - w / 2, plot_h - top))
            w, h = _drawings.inches2axes(ax0, (w, h))
            rect = patches.Rectangle(xy, color='k', width=w, height=h)
            ax0.add_artist(rect)

            left += segment_top_size
            left_xy += segment_top_size * xy_per_inch

        # нижняя линия
        inches_per_lon_deg_bottom = raster_w / (br[0] - bl[0])
        degrees_per_segment_bottom = math.ceil(self.map_mark_degree_seg_len / inches_per_lon_deg_bottom * 3600) / 3600
        segment_bottom_size = min(degrees_per_segment_bottom * inches_per_lon_deg_bottom, raster_w / 2)
        segments_count_bottom = int(raster_w // segment_bottom_size)

        # начинаем рисовать нижнюю линию
        top = self.outer_size[0] + raster_h
        offset_x = (raster_w - (segments_count_bottom - 1) * segment_top_size) / 2
        left = self.outer_size[3] + offset_x
        left_xy = tl_xy[0] + xy_per_inch * offset_x
        del offset_x

        for i in range(segments_count_bottom):
            w, h = self.map_latlong_mark_thickness, self.map_latlon_mark_len
            xy = _drawings.inches2axes(ax0, (left - w / 2, plot_h - top - h - cm(.1)))
            long = utility.transform_point(src_crs, 'EPSG:4326', (left_xy, transform.f + transform.e * file.height))[0]
            degree, minutes, seconds = _split_degree(long)
            _drawings.draw_text(f'{degree}°{minutes}\'{seconds}\'\'',
                                (left + cm(.05), plot_h - h - top - cm(.15)), ax0, va='top', ha='center', fontsize=14,
                                fontproperties=fontprops)

            w, h = _drawings.inches2axes(ax0, (w, h))
            rect = patches.Rectangle(xy, color='k', width=w, height=h)
            ax0.add_artist(rect)

            left += segment_top_size
            left_xy += segment_top_size * xy_per_inch

        # левая линия
        inches_per_lat_deg_left = raster_h / (tl[0] - bl[0])
        degrees_per_segment_left = math.ceil(self.map_mark_degree_seg_len / inches_per_lat_deg_left * 3600) / 3600
        segment_left_size = min(degrees_per_segment_left * inches_per_lat_deg_left, raster_h / 2)
        segments_count_left = int(raster_h // segment_left_size)

        # начинаем рисовать левую линию
        left = self.outer_size[3] - self.map_latlon_mark_len
        offset_y = (raster_h - (segments_count_left - 1) * segment_left_size) / 2
        top = self.outer_size[0] + offset_y
        top_xy = tl_xy[1] + xy_per_inch * offset_y
        del offset_y

        for i in range(segments_count_left):
            h, w = self.map_latlong_mark_thickness, self.map_latlon_mark_len
            xy = _drawings.inches2axes(ax0, (left - h, plot_h - top - h / 2))
            long = utility.transform_point(src_crs, 'EPSG:4326', (transform.c, transform.f + top_xy))[1]
            degree, minutes, seconds = _split_degree(long)
            _drawings.draw_text(f'{degree}°{minutes}\'{seconds}\'\'',
                                (left - cm(.1), plot_h - top), ax0, va='center', ha='right',
                                rotation=90, fontsize=14, fontproperties=fontprops)

            w, h = _drawings.inches2axes(ax0, (w, h))
            rect = patches.Rectangle(xy, color='k', width=w, height=h)
            ax0.add_artist(rect)

            top += segment_left_size
            top_xy += segment_left_size * xy_per_inch

        # правая линия
        inches_per_lat_deg_right = raster_h / (tr[0] - br[0])
        degrees_per_segment_right = math.ceil(self.map_mark_degree_seg_len / inches_per_lat_deg_right * 3600) / 3600
        segment_right_size = min(degrees_per_segment_right * inches_per_lat_deg_right, raster_h / 2)
        segments_count_right = int(raster_h // segment_right_size)

        # начинаем рисовать правую линию
        left = self.outer_size[3] + raster_w
        offset_y = (raster_h - (segments_count_right - 1) * segment_right_size) / 2
        top = self.outer_size[0] + offset_y
        top_xy = tl_xy[1] + xy_per_inch * offset_y
        del offset_y

        for i in range(segments_count_right):
            h, w = self.map_latlong_mark_thickness, self.map_latlon_mark_len
            xy = _drawings.inches2axes(ax0, (left, plot_h - top - h / 2))
            long = utility.transform_point(src_crs, 'EPSG:4326', (transform.c, transform.f + top_xy))[1]
            degree, minutes, seconds = _split_degree(long)
            _drawings.draw_text(f'{degree}°{minutes}\'{seconds}\'\'',
                                (left + h + cm(.4), plot_h - top), ax0, va='center', ha='left',
                                rotation=90, fontsize=14, fontproperties=fontprops)

            w, h = _drawings.inches2axes(ax0, (w, h))
            rect = patches.Rectangle(xy, color='k', width=w, height=h)
            ax0.add_artist(rect)

            top += segment_right_size
            top_xy += segment_right_size * xy_per_inch

