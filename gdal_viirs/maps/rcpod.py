import math

from matplotlib import patches, lines
from matplotlib.colors import ListedColormap, BoundaryNorm

from gdal_viirs.maps import _drawings
from gdal_viirs.maps.builder import MapBuilder, cm

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
    spacecraft_name = ''
    iso_sign_path = None
    logo_path = None
    gradation_value = None

    def __init__(self, file, **kwargs):
        super(RCPODMapBuilder, self).__init__(file, **kwargs)
        self.margin = cm(1)
        self.outer_size = cm(6.5), self.margin * 2, cm(10), self.margin + cm(17)
        self.min_height = cm(26)
        self.min_width = cm(22)
        self.max_width = cm(50)
        self.max_height = cm(50)

        # настройка параметров для меток на карте
        self.map_mark_min_length = cm(1)  # минимальная длина сегмента обозначения длинны
        self.map_mark_max_length = cm(2.5)  # максимальная длина сегмента обозначения длинны
        self.map_mark_thickness = cm(.25)  # толщина сегмента
        self.map_mark_dist = 1, 1, 2, 2, 3  # длинная сегментов, измеренная в процентах по сравнению с минимальной
        self.map_mark_colors = 'black', 'white'  # чередующиеся цвета сегментов

        self.map_mark_degree_seg_len = cm(5)  # минимальное растояние между отметками градусов на карте
        self.map_latlong_mark_thickness = cm(.1)  # толщина отметок
        self.map_latlon_mark_len = cm(.35)  # длинна отметок

        self.init()

    def init(self):
        pass

    def get_legend_handles(self):
        return []

    def get_secondary_legend_handles(self):
        handles = [
            lines.Line2D([], [], linewidth=2, color=REGIONS_BORDER_COLOR, label='Границы районов'),
            lines.Line2D([], [], linewidth=4, color=STATES_BORDER_COLOR, label='Границы субъектов РФ'),
            lines.Line2D([], [], marker='o', markersize=13.3, markerfacecolor='white', color='none',
                         markeredgecolor='k', linewidth=2, label='Населенные пункты'),
        ]
        if self.water_shp_file is not None:
            handles.append(patches.Patch(color='#004da8', label='Водоёмы'))
        return handles

    def plot(self):
        fig, (ax0, ax1) = super(RCPODMapBuilder, self).plot()
        logo_size = cm(3)  # размер лого - 75% от толщины верхней зоны
        logo_padding = cm(.7)  #
        size = self._raster_area

        # рисуем логотип в верхнем левом углу
        if self.logo_path:
            _drawings.draw_image(self.logo_path, (self.margin + logo_padding, logo_padding + cm(.5)), ax0,
                                 max_width=logo_size, max_height=logo_size,
                                 origin=_drawings.TOP_LEFT)
        _drawings.draw_image(self.iso_sign_path, (self.margin, self.margin), ax0,
                             max_width=cm(2), max_height=cm(2),
                             origin=_drawings.BOTTOM_RIGHT)

        title_width = fig.get_size_inches()[0] - self.margin * 2 - logo_padding - logo_size
        _drawings.draw_text('ФЕДЕРАЛЬНАЯ СЛУЖБА ПО ГИДРОМЕТЕОРОЛОГИИ И МОНИТОРИНГУ ОКРУЖАЮЩЕЙ СРЕДЫ\n'
                            'ФГБУ "НАУЧНО-ИССЛЕДОВАТЕЛЬСКИЙ ЦЕНТР КОСМИЧЕСКОЙ ГИДРОМЕТЕОРОЛОГИИ "ПЛАНЕТА"\n'
                            'СИБИРСКИЙ ЦЕНТР',
                            (self.margin * 2 + logo_padding + logo_size + title_width / 2,
                             logo_padding + cm(.5)), ax0,
                            max_size=(title_width, self.outer_size[0]),
                            wrap=True, fontproperties=self._get_font_props(size=25.5),
                            va='top', ha='center', origin=_drawings.TOP_LEFT)
        _drawings.draw_text('\n'.join([
            'Сибирский центр',
            'ФГБУ НИЦ «ПЛАНЕТА»',
            'Россия, 630099, г. Новосибирск',
            'ул. Советская, 30',
            'Тел. (383) 363-46-05',
            'Факс. (383) 363-46-05',
            'E-mail: kav@rcpod.siberia.net',
            'http://www.rcpod.ru'
        ]), (self.margin, self.margin), ax0, fontproperties=self._get_font_props(size=18), va='bottom', ha='left')

        _drawings.draw_text(self.bottom_title + '\n' + (self.bottom_subtitle or ''),
                            (self.outer_size[3] + size[0] / 2, self.margin + cm(2)), ax0,
                            max_size=(size[0] - cm(2), cm(6)),
                            ha='center', va='center', wrap=True, fontproperties=self._get_font_props(size=36))

        if self.date_text:
            _drawings.draw_text(self.date_text,
                                (fig.get_size_inches()[0] - self.outer_size[1], self.margin * 1.3 + cm(5)),
                                ax0, ha='right', va='bottom',
                                fontproperties=self._get_font_props(size=26))

        self._draw_legend(ax0)
        self._draw_scale_line(ax0)

        return fig, (ax0, ax1)

    def _draw_legend(self, ax0):
        """
        Рисуем легенду для изображенния и некоторый текст
        """
        top = self.outer_size[0] + self.margin  # отступ сверху

        l = _drawings.LinearLayout(ax0, (self.outer_size[3] / 2, top), origin=_drawings.TOP_LEFT)
        l.set_spacing(cm(.6))
        l.text(self.spacecraft_name, fontproperties=self._get_font_props(size=28))
        l.text('Разрешение 375 м', fontproperties=self._get_font_props(size=22))
        l.spacing(cm(.9))
        l.text('Условные обозначения', fontproperties=self._get_font_props(size=26))
        l.spacing(cm(.4))
        l.legend(handles=self.get_secondary_legend_handles(), edgecolor='none', prop=self._get_font_props(size=20))
        l.text('Состояние посевов', fontproperties=self._get_font_props(size=22))
        l.legend(handles=self.get_legend_handles(), edgecolor='none', prop=self._get_font_props(size=20))

    @property
    def _inches_per_km(self):
        plot_width = self._raster_size_rect[0][0]
        xlim = self._lims[0]
        km_width = abs(xlim[0] - xlim[1]) / 1000
        return plot_width / km_width

    def _draw_scale_line(self, ax):
        fontprops = self._get_font_props(size=16)
        # расчитываем, сколько дюймов должно приходится на один сегмент
        inches_per_unit_x = self._inches_per_km
        units_per_segment = self.map_mark_min_length / inches_per_unit_x
        unit = 'км'

        if units_per_segment < 1:
            # на один сегмент приходится менее 1 км
            if inches_per_unit_x < self.map_mark_max_length:
                # если один сегмент равен 1 км и сегмент не становится слишком большим, сделаем 1 км на сегмент
                units_per_segment = 1
            else:
                # ...иначе поменяем ед. изменерения на метры
                units_per_segment = math.floor(units_per_segment * 1000)
                unit = 'м'
                inches_per_unit_x /= 1000
        else:
            units_per_segment = math.floor(units_per_segment)

        if units_per_segment > 30 and units_per_segment % 10 != 0:
            units_per_segment = round(units_per_segment / 10) * 10
        inches_per_segment = units_per_segment * inches_per_unit_x

        y = self.outer_size[2] - self.margin * 1.5 - self.map_mark_thickness
        km_width = _drawings.draw_text(unit, (self.outer_size[1], y + self.map_mark_thickness / 2), ax,
                                       origin=_drawings.BOTTOM_RIGHT, fontproperties=fontprops,
                                       align=_drawings.Alignment(hor=_drawings.RIGHT, ver=_drawings.VCENTER))[0]

        left_offset = left = self.outer_size[3] + self._get_plot_area(ax.figure.get_size_inches())[
            0] - inches_per_segment * sum(
            self.map_mark_dist) - km_width - cm(.2)
        odd = True
        km = 0

        # рисуем отметки по указанным значениям распределения
        # Напремер, если self.map_mark_dist = (1, 2, 3, 2, 5), это значит, что будет 5
        # отметок, первая будет иметь длинну 100%, вторая 200% и т. д.
        for dist in self.map_mark_dist:
            km += units_per_segment * dist
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
