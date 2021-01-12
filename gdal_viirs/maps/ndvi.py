import math
import cartopy
import numpy as np

from matplotlib.colors import ListedColormap, BoundaryNorm
from rasterio import DatasetReader
from matplotlib import rcParams, patches, lines

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


class NDVIMapBuilder(MapBuilder):
    """
    Данная реализация класса MapBuilder предназначена для отображения NDVI карты
    с отмечание городов, водоёмов и значений NDVI со следующими значениями:
        * "Хорошо" >= 0.7
        * "Удовлетворительно" >= 0.3
        * "Плохо" >= -1
        * "Закрыто облаками" = -2
        * "Водоёмы" = -4
    """

    bottom_title = 'Мониторинг состояния посевов зерновых культур'
    bottom_subtitle = None

    def __init__(self, logo_path='./logo.png', map_points=None, **kwargs):
        super(NDVIMapBuilder, self).__init__(**kwargs)
        points.add_points(self, [
            *points.SIBERIA_CITIES,
            *(map_points or []),
        ])
        self.margin = cm(1)
        self.cmap = ListedColormap(['#aaa', "red", "yellow", 'greenyellow'])
        self.norm = BoundaryNorm([-2, -1, .4, .7], 4)
        self.outer_size = cm(6), self.margin, cm(7), self.margin + cm(13)
        self.min_height = cm(30)

        self.logo_path = logo_path

        # настройка параметров для меток на карте
        self.map_mark_min_length = cm(1)  # минимальная длина сегмента обозначения длинны
        self.map_mark_thickness = cm(.25)  # толщина сегмента
        self.map_mark_dist = 1, 1, 2, 2, 3  # длинная сегментов, измеренная в процентах по сравнению с минимальной
        self.map_mark_colors = 'black', 'white'  # чередующиеся цвета сегментов

        self.map_mark_degree_seg_len = cm(5)  # минимальное растояние между отметками градусов на карте
        self.map_latlong_mark_thickness = cm(.1)  # толщина отметок
        self.map_latlon_mark_len = cm(.35)  # длинна отметок

    def plot(self, file: DatasetReader, band=1):
        fig, (ax0, ax1), size = super(NDVIMapBuilder, self).plot(file, band)
        top_gap = self.outer_size[0]
        logo_size = top_gap * .75  # размер лого - 75% от толщины верхней зоны
        logo_padding = top_gap * .0375 #

        # рисуем логотип в верем левом углу
        _drawings.draw_image(self.logo_path, (self.margin + logo_padding, logo_padding + cm(.5)), ax0,
                             max_width=logo_size, max_height=logo_size,
                             origin=_drawings.TOP_LEFT)

        text_left = self.margin + logo_size + logo_padding*2 + cm(.75)  # отступ текста слева
        _drawings.draw_text('ФГБУ «НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ЦЕНТР КОСМИЧЕСКОЙ ГИДРОМЕТЕОРОЛОГИИ «ПЛАНЕТА»\nСИБИРСКИЙ ЦЕНТР',
                            (text_left, cm(1.5)), ax0,
                            wrap=True, fontproperties=self._get_font_props(size=24), va='top', ha='left', invert_y=True)
        _drawings.draw_text('\n'.join([
            'Сибирский центр',
            'ФГБУ НИЦ «ПЛАНЕТА»',
            'Россия, 630099, г. Новосибирск',
            'ул. Советская, 30',
            'Тел. (383) 363-46-05',
            'Факс. (383) 363-46-05',
            'E-mail: kav@rcpod.siberia.net',
            'http://rcpod.ru'
        ]), (self.margin, self.margin), ax0, fontproperties=self._get_font_props(size=16), va='bottom', ha='left')
        _drawings.draw_text(self.bottom_title + '\n' + (self.bottom_subtitle or ''),
                            (self.outer_size[3], self.outer_size[2] / 2), ax0,
                            ha='left', va='top', weight='bold',
                            fontproperties=self._get_font_props(size=30, weight='bold'))

        data = file.read(band)#utility.apply_xy_lim(file.read(band), file.transform, *self._get_lims(file))
        self._draw_legend(ax0, data)
        del data
        self._draw_map_marks(ax0, file)

        return fig, (ax0, ax1), size

    def get_projection(self, file):
        return cartopy.crs.LambertConformal(
            standard_parallels=(67.41206675, 43.58046825),
            central_longitude=80,
            central_latitude=55.4962675
        )

    def _draw_legend(self, ax0, data):
        """
        Рисуем легенду для изображенния и некоторый текст
        """
        fontprops = self._get_font_props(size=20)
        top = self.outer_size[0] + self.margin  # отступ сверху
        _drawings.draw_text('Suomi NPP/VIIRS', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', weight='bold', fontsize=23, invert_y=True,
                            fontproperties=self._get_font_props(size=28))
        top += self.margin * 2
        _drawings.draw_text('Состояние посевов', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', invert_y=True,
                            fontproperties=fontprops)
        top += cm(8)
        loc = _drawings.inches2axes(ax0, (self.margin, top))
        loc = loc[0], 1 - loc[1]

        data_mask = ~np.isnan(data) * (data >= -1)
        all_count = np.count_nonzero(data_mask)
        bad_count = np.count_nonzero(data_mask * (data < 0.3))
        ok_count = np.count_nonzero(data_mask * (data < 0.7) * (data >= 0.3))
        good_count = np.count_nonzero(data_mask * (data >= 0.7))
        leg1 = ax0.legend(handles=[
            patches.Patch(color='red', label=f'Плохое\n< 0.3 ({round(100 * bad_count / all_count)}%)'),
            patches.Patch(color='yellow', label=f'Удовлетворительное\n< 0.7 ({round(100 * ok_count / all_count)}%)'),
            patches.Patch(color='greenyellow', label=f'Хорошое\n>= 0.7 ({round(100 * good_count / all_count)}%)'),
            patches.Patch(color='#aaa', label='Закрыто облаками'),
        ], loc=loc, edgecolor='none', fontsize=20, prop=fontprops)

        top += cm(1)

        _drawings.draw_text('Условные обозначения', (self.outer_size[3] / 2, top), ax0,
                            ha='center', va='top', fontsize=20, invert_y=True, fontproperties=fontprops)

        top += cm(6)
        loc = _drawings.inches2axes(ax0, (self.margin, top))
        loc = loc[0], 1 - loc[1]
        ax0.legend(handles=[
            lines.Line2D([], [], linewidth=2, color='k', linestyle='-.', label='Границы субъектов'),
            lines.Line2D([], [], linewidth=4, color='k', label='Границы стран'),
            lines.Line2D([], [], marker='o', markersize=20, markerfacecolor=self.points_color, color='none',
                         markeredgecolor=self.points_color, linewidth=2, label='Населенные пункты'),
            patches.Patch(color='blue', label='Водоёмы'),
        ], loc=loc, edgecolor='none', prop=fontprops)
        ax0.add_artist(leg1)

    def _get_pixels_per_km(self, file: DatasetReader):
        pixels_per_km_x = 1000 / file.transform.a
        xlim = self._get_lims(file)[0]
        zoom = abs(xlim[0] - xlim[1]) / (file.transform.a * file.width)
        pixels_per_km_x /= zoom
        return pixels_per_km_x

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
        transform = file.transform
        fontprops = self._get_font_props()

        # расчитываем, сколько дюймов должно приходится на один сегмент
        pixels_per_km_x = self._get_pixels_per_km(file)
        inches_per_km_x = pixels_per_km_x / ax0.figure.dpi
        km_per_segment = math.floor(self.map_mark_min_length / inches_per_km_x)
        if km_per_segment > 30 and km_per_segment % 10 != 0:
            km_per_segment = round(km_per_segment / 10) * 10
        inches_per_segment = km_per_segment * inches_per_km_x

        left = self.outer_size[3]
        odd = True
        km = 0
        y = self.outer_size[2] - self.margin * 2 - self.map_mark_thickness

        # рисуем отметки по указанным значениям распределения
        # Напремер, если self.map_mark_dist = (1, 2, 3, 2, 5), это значит, что будет 5
        # отметок, первая будет иметь длинну 100%, вторая 200% и т. д.
        for dist in self.map_mark_dist:
            km += km_per_segment * dist
            w_inches = dist * inches_per_segment
            w, h = _drawings.inches2axes(ax0, (w_inches, self.map_mark_thickness))
            xy = _drawings.inches2axes(ax0, (left, y))
            color = self.map_mark_colors[0] if odd else self.map_mark_colors[1]
            rect1 = patches.Rectangle(xy, color=color, width=w, height=h)
            ax0.add_artist(rect1)
            _drawings.draw_text(str(km), (left + w_inches, y - h - cm(.1)), ax0, va='top', ha='right',
                                fontproperties=fontprops)
            left += w_inches
            odd = not odd

        # рисуем окантовку
        # TODO цвет окантовки
        _drawings.draw_rect_with_outside_border((self.outer_size[3], y),
                                                sum(self.map_mark_dist) * inches_per_segment,
                                                self.map_mark_thickness, ax0)

        # отметки в грудусах
        src_crs = file.crs.to_proj4()
        xlim, ylim = self._get_lims(file)
        points = utility.transform_points(src_crs, 'EPSG:4326', (
            (xlim[0], ylim[0]),
            (xlim[1], ylim[0]),
            (xlim[0], ylim[1]),
            (xlim[1], ylim[1])
        ))
        bl, br, tl, tr = points

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
        left_xy = tl[0] + xy_per_inch * offset_x
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
        left_xy = tl[0] + xy_per_inch * offset_x
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
        top_xy = tl[1] + xy_per_inch * offset_y
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
        top_xy = tl[1] + xy_per_inch * offset_y
        del offset_y

        for i in range(segments_count_left):
            h, w = self.map_latlong_mark_thickness, self.map_latlon_mark_len
            xy = _drawings.inches2axes(ax0, (left, plot_h - top - h / 2))
            long = utility.transform_point(src_crs, 'EPSG:4326', (transform.c, transform.f + top_xy))[1]
            degree, minutes, seconds = _split_degree(long)
            _drawings.draw_text(f'{degree}°{minutes}\'{seconds}\'\'',
                                (left + h + cm(.2), plot_h - top), ax0, va='center', ha='left',
                                rotation=-90, fontsize=14, fontproperties=fontprops)

            w, h = _drawings.inches2axes(ax0, (w, h))
            rect = patches.Rectangle(xy, color='k', width=w, height=h)
            ax0.add_artist(rect)

            top += segment_left_size
            top_xy += segment_left_size * xy_per_inch

