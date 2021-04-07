import os
import time
from functools import lru_cache
from typing import Tuple, Optional

import cartopy
import cartopy.io.shapereader
import cartopy.mpl.gridliner
import matplotlib.font_manager as _fm
import numpy as np
import rasterio.plot
from PIL import Image, PngImagePlugin
from adjustText import adjust_text
from loguru import logger
from matplotlib import pyplot, patches, offsetbox, patheffects
from matplotlib.colors import to_rgb
from matplotlib.ticker import Formatter
from rasterio import DatasetReader

from gdal_viirs import misc
from gdal_viirs.maps.utils import CARTOPY_LCC, get_lonlat_lim_range
from gdal_viirs.types import Number

_CM = 1 / 2.54

__all__ = (
    'build_figure',
    'MapBuilder'
)


def cm(v):
    return v * _CM


def _split_degree(deg):
    degree = int(deg)
    deg -= degree
    deg *= 60
    minutes = int(deg)
    deg -= minutes
    deg *= 60
    seconds = int(deg)
    return degree, minutes, seconds


class DegreeFormatter(Formatter):
    def __init__(self, is_lat: bool):
        super(DegreeFormatter, self).__init__()
        self.is_lat = is_lat

    def __call__(self, x, pos=None):
        deg, minutes, seconds = _split_degree(x)
        r = f'{deg}°'
        if minutes or seconds:
            if minutes <= 9:
                r += '0'
            r += f'{minutes}\''

        if self.is_lat:
            prefix = 'Ю' if x < 0 else 'С'
        else:
            prefix = 'З' if x < 0 else 'В'

        r += prefix

        return r


LONGITUDE_FORMATTER = DegreeFormatter(False)
LATITUDE_FORMATTER = DegreeFormatter(True)


def _gridlines_with_labels(ax, top=True, bottom=True, left=True,
                           right=True, **kwargs):
    """
    https://gist.github.com/jnhansen/eff9e011da86760a18f886eab9cc1d31
    """

    # Add gridlines
    gridliner = ax.gridlines(**kwargs)

    ax.tick_params(length=0)

    # Get projected extent
    xmin, xmax, ymin, ymax = ax.get_extent()

    # Determine tick positions
    sides = {}
    N = 500
    if bottom:
        sides['bottom'] = np.stack([np.linspace(xmin, xmax, N),
                                    np.ones(N) * ymin])
    if top:
        sides['top'] = np.stack([np.linspace(xmin, xmax, N),
                                 np.ones(N) * ymax])
    if left:
        sides['left'] = np.stack([np.ones(N) * xmin,
                                  np.linspace(ymin, ymax, N)])
    if right:
        sides['right'] = np.stack([np.ones(N) * xmax,
                                   np.linspace(ymin, ymax, N)])

    # Get latitude and longitude coordinates of axes boundary at each side
    # in discrete steps
    gridline_coords = {}
    for side, values in sides.items():
        gridline_coords[side] = cartopy.crs.PlateCarree().transform_points(
            ax.projection, values[0], values[1])

    lon_lim, lat_lim = get_lonlat_lim_range((xmin, xmax, ymin, ymax), ax.projection)
    ticklocs = {
        'x': gridliner.xlocator.tick_values(lon_lim[0], lon_lim[1]),
        'y': gridliner.ylocator.tick_values(lat_lim[0], lat_lim[1])
    }

    # Compute the positions on the outer boundary where
    coords = {}
    for name, g in gridline_coords.items():
        if name in ('bottom', 'top'):
            compare, axis = 'x', 0
        else:
            compare, axis = 'y', 1
        coords[name] = np.array([
            sides[name][:, np.argmin(np.abs(
                gridline_coords[name][:, axis] - c))]
            for c in ticklocs[compare]
        ])

    # Create overlay axes for top and right tick labels
    ax_topright = ax.figure.add_axes(ax.get_position(), frameon=False)
    ax_topright.tick_params(
        left=False, labelleft=False,
        right=True, labelright=True,
        bottom=False, labelbottom=False,
        top=True, labeltop=True,
        length=0
    )
    ax_topright.set_xlim(ax.get_xlim())
    ax_topright.set_ylim(ax.get_ylim())

    for side, tick_coords in coords.items():
        if side in ('bottom', 'top'):
            axis, idx = 'x', 0
        else:
            axis, idx = 'y', 1

        _ax = ax if side in ('bottom', 'left') else ax_topright

        ticks = tick_coords[:, idx]

        valid = np.logical_and(
            ticklocs[axis] >= gridline_coords[side][0, idx],
            ticklocs[axis] <= gridline_coords[side][-1, idx])

        if side in ('bottom', 'top'):
            _ax.set_xticks(ticks[valid])
            _ax.set_xticklabels([LONGITUDE_FORMATTER.format_data(t)
                                 for t in np.array(ticklocs[axis])[valid]], rotation=0, fontsize=17)
        else:
            _ax.set_yticks(ticks[valid])
            _ax.set_yticklabels([LATITUDE_FORMATTER.format_data(t)
                                 for t in np.array(ticklocs[axis])[valid]], rotation=90, fontsize=17)

    return gridliner


def build_figure(data, axes, crs, *, xlim: Tuple[Number, Number] = None, ylim: Tuple[Number, Number] = None, cmap=None,
                 norm=None, transform=None,
                 water_shp_file=None, water_color='#004da8', layers=None):
    rasterio.plot.show(data, cmap=cmap, norm=norm, ax=axes, interpolation='none', transform=transform)

    if water_shp_file:
        water_feature = cartopy.feature.ShapelyFeature(
            cartopy.io.shapereader.Reader(water_shp_file).geometries(),
            crs=crs,
            fc=water_color, ec=water_color, lw=0
        )
        axes.add_feature(water_feature)

    if layers:
        for layer in layers:
            if isinstance(layer, cartopy.feature.Feature):
                axes.add_feature(layer)
            else:
                layer = layer.copy()
                if 'crs' in layer:
                    crs = layer['crs']
                    del layer['crs']
                else:
                    crs = CARTOPY_LCC
                file = layer['file']
                del layer['file']
                layer['fc'] = layer.get('fc', 'none')
                feature = cartopy.feature.ShapelyFeature(
                    cartopy.io.shapereader.Reader(file).geometries(),
                    crs=crs, **layer
                )
                axes.add_feature(feature)

    if xlim:
        axes.set_xlim(xlim)
    if ylim:
        axes.set_ylim(ylim)

    axes.set_extent([
        xlim[0], xlim[1], ylim[0], ylim[1]
    ], crs=crs)

    pyplot.yticks(rotation='vertical')
    _gridlines_with_labels(axes)
    return axes


def plot_marks(points: dict, crs, ax, ec='k', fc='white', props=None):
    plate_carree = cartopy.crs.PlateCarree()
    annotations = []
    for coord, text in points.items():
        point = crs.transform_point(coord[0], coord[1], plate_carree)
        ax.plot(*point, color='none', markersize=10, marker='o', markeredgewidth=2, markeredgecolor=to_rgb(ec),
                markerfacecolor=to_rgb(fc))
        text = ax.annotate(text, point, fontsize=23, fontproperties=props)
        text.set_path_effects([patheffects.withStroke(linewidth=3, foreground='w')])
        text.set_clip_on(True)
        annotations.append(text)
    adjust_text(annotations)


def _plot_rect_with_outside_border(image_pos_ax, plot_size_ax, ax):
    frame = patches.Rectangle((*image_pos_ax, 0), *plot_size_ax, facecolor='none')
    offbox = offsetbox.AuxTransformBox(ax.transData)
    offbox.add_artist(frame)
    ab = offsetbox.AnnotationBbox(offbox,
                                  (image_pos_ax[0] + plot_size_ax[0] / 2., image_pos_ax[1] + plot_size_ax[1] / 2.),
                                  boxcoords="data", pad=0.52, fontsize=2,
                                  bboxprops=dict(fc="none", ec='k', lw=2))
    ax.add_artist(ab)


class MapBuilder:
    xlim: Optional[Tuple[Number, Number]]
    ylim: Optional[Tuple[Number, Number]]
    cartopy_scale: str
    cmap = None
    norm = None
    points_color = '#7F00FF'
    font_size = 25
    outer_size: Tuple[Number, Number, Number, Number] = (cm(.5), cm(.5), cm(.5), cm(.5))
    dpi = 100
    expected_width = None
    expected_height = None
    min_raster_area_size = cm(10), cm(10)
    font_family = None
    agro_mask_shp_file = None
    water_shp_file = None
    layers = None

    def __init__(self, file: DatasetReader, band=1, **kwargs):
        self.points = {}
        self.cartopy_scale = '10m'
        self.file = file
        self.band = band

        self.xlim = None
        self.ylim = None

        if 'points' in kwargs:
            for p in kwargs['points']:
                self.add_point(*p)
            del kwargs['points']

        for k, v in kwargs.items():
            if k.startswith('_'):
                continue
            if hasattr(self, k):
                setattr(self, k, v)

    def read_data(self):
        if not hasattr(self, '_data'):
            setattr(self, '_data', self.file.read(self.band))
        return getattr(self, '_data')

    def _get_font_props(self, **kwargs):
        if self.font_family:
            if os.path.isfile(self.font_family):
                kwargs['fname'] = self.font_family
        return _fm.FontProperties(**kwargs)

    def add_point(self, lat: Number, lon: Number, text: str):
        self.points[(lon, lat)] = text

    def plot(self):
        xlim, ylim = self._lims  # границы растра в координатах проекции
        size = self._full_plot_size
        fig = pyplot.figure(figsize=size, dpi=self.dpi)
        data = self.read_data()
        crs = self.get_projection()

        # получаем реальный размер
        image_size, image_pos = self._raster_size_rect

        # сконвертировать координаты изображения в пиксели (можно просто помножить на dpi)
        image_pos_px = fig.dpi_scale_trans.transform((image_pos[0], size[1] - image_pos[1] - image_size[
            1]))  # позиция изображеня в пикселях, от вернего левого угла
        image_pos_ax = fig.transFigure.inverted().transform(image_pos_px)  # в долях(?) (от 0 до 1)
        plot_size_ax = fig.transFigure.inverted().transform(fig.dpi_scale_trans.transform(image_size))
        ax0 = fig.add_axes([0, 0, 1, 1])
        ax0.set_axis_off()
        ax1 = fig.add_axes([*image_pos_ax, *plot_size_ax], projection=crs)

        self._build_figure(data, crs, ax1, xlim, ylim)
        plot_marks(self.points, crs, ax1)

        return fig, (ax0, ax1)

    def _build_figure(self, data, crs, ax1, xlim, ylim):
        build_figure(data, ax1, crs, cmap=self.cmap, norm=self.norm, xlim=xlim, ylim=ylim,
                     transform=self.file.transform,
                     water_shp_file=self.water_shp_file,
                     layers=self.layers)

    @property
    @lru_cache()
    def _full_plot_size(self) -> Tuple[Number, Number]:
        if self.expected_height is None or self.expected_width is None:
            return self._guess_size()
        w, h = self.expected_width, self.expected_height
        if w <= 0:
            logger.error('ширина (expected_width) меньше или равна 0, размер изображения будет определен автоматически')
            return self._guess_size()

        if h <= 0:
            logger.error(
                'высота (expected_height) меньше или равна 0, размер изображения будет определен автоматически')
            return self._guess_size()

        if hasattr(self, '_cached_size'):
            return self._cached_size

        # подсчитывем размер зоны для растра на карте и если
        # этот размер меньше, чем минимальный увеличиваем размер всей карты и кидаем варнинг в консоль
        plot_size = self._get_plot_area((w, h))
        if plot_size[0] < self.min_raster_area_size[0]:
            logger.warning('ширина зоны для размещения растра на карте меньше минимальной ({} < {})',
                           plot_size[0], self.min_raster_area_size[0])
            zoom = (w + self.min_raster_area_size[0] - plot_size[0]) / w
            w *= zoom
            h *= zoom
            plot_size = self._get_plot_area((w, h))

        if plot_size[1] < self.min_raster_area_size[1]:
            logger.warning('высота зоны для размещения растра на карте меньше минимальной ({} < {})',
                           plot_size[1], self.min_raster_area_size[1])
            zoom = (h + self.min_raster_area_size[1] - plot_size[1]) / h
            w *= zoom
            h *= zoom
        setattr(self, '_cached_size', (w, h))
        return w, h

    def _guess_size(self) -> Tuple[Number, Number]:
        plot_size = self._raster_size_inches
        size = plot_size[0] + self.outer_size[1] + self.outer_size[3], \
               plot_size[1] + self.outer_size[0] + self.outer_size[2]

        return size

    @property
    def _raster_area(self):
        return self._get_plot_area(self._full_plot_size)

    def _get_plot_area(self, size):
        return size[0] - self.outer_size[1] - self.outer_size[3], \
               size[1] - self.outer_size[0] - self.outer_size[2]

    def _get_point_fontprops(self):
        return self._get_font_props(size=16)

    def plot_to_file(self, output_file: str):
        figure, _1 = self.plot()
        figure.savefig(output_file, bbox_inches=None, pad_inches=0, transparent=False)
        pyplot.close(figure)

        if output_file.endswith('.png'):
            try:
                meta = self.get_image_metadata()
                if len(meta) == 0:
                    return

                im = Image.open(output_file)
                meta = PngImagePlugin.PngInfo()

                for x in meta:
                    meta.add_text(x, meta[x])
                im.save(output_file, "png", pnginfo=meta)
            except Exception as exc:
                logger.warning(f'Не удалось записать метаданные в файл изображения: {exc}')

    def get_image_metadata(self):
        return {}

    def get_projection(self):
        return CARTOPY_LCC

    @property
    @lru_cache()
    def _lims(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        xlim = self.xlim or (self.file.transform.c, self.file.transform.a * self.file.width + self.file.transform.c)
        ylim = self.ylim or (self.file.transform.e * self.file.height + self.file.transform.f, self.file.transform.f)
        return xlim, ylim

    @property
    @lru_cache()
    def _raster_size_inches(self):
        """
        Подсчитывает сколько будет занимать места растр без масштабирования.
        :return: кортеж (ширина, высота)
        """
        xlim, ylim = self._lims
        plot_width = abs(xlim[0] - xlim[1]) / self.file.transform.a / self.dpi
        plot_height = abs(ylim[0] - ylim[1]) / self.file.transform.a / self.dpi
        return plot_width, plot_height

    @property
    @lru_cache()
    def _raster_size_rect(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Подсчитывает, где находится изображение растра и какого оно должно быть размера.
        :return: Два кортежа. Первый - размер изображения в соответсвии с масштабированием. Второй -
        местоположение изображения на на конечной карте (все в дюймах).
        """
        # получаем реальный размер
        plot_size = self._raster_size_inches
        plot_ratio = plot_size[0] / plot_size[1]
        del plot_size

        area_size = self._raster_area
        area_ratio = area_size[0] / area_size[1]

        if area_ratio > plot_ratio:
            # зона, где должна находится карта шире, чем сама карта,
            # следовательно, нужно растянуть карту по высоте и отцентровать по ширине
            image_size = area_size[1] * plot_ratio, area_size[1]
            image_pos = self.outer_size[3] + (area_size[0] - image_size[0]) / 2, self.outer_size[0]
        elif area_ratio < plot_ratio:
            # отцентровать по высоте, растянуть по ширине
            image_size = area_size[0], area_size[0] / plot_ratio
            image_pos = self.outer_size[3], self.outer_size[0] + (area_size[1] - image_size[1]) / 2
        else:
            image_pos = self.outer_size[3], self.outer_size[0]
            image_size = area_size
        return image_size, image_pos
