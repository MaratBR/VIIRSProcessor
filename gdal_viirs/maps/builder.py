import os

import matplotlib.font_manager as _fm
import rasterio.plot
from adjustText import adjust_text
import numpy as np
from matplotlib.colors import to_rgb
from matplotlib.ticker import Formatter

from gdal_viirs.config import req_resource_path
from gdal_viirs.hl import points
from gdal_viirs.maps.cartopy_utils import CARTOPY_LCC, get_lonlat_lim_range
from gdal_viirs.types import Number
from typing import Tuple, Optional
from rasterio import DatasetReader
from matplotlib import pyplot, patches, offsetbox, patheffects
import cartopy
import cartopy.mpl.gridliner
import cartopy.io.shapereader

_CM = 1/2.54

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
                                 for t in np.array(ticklocs[axis])[valid]], rotation=0)
        else:
            _ax.set_yticks(ticks[valid])
            _ax.set_yticklabels([LATITUDE_FORMATTER.format_data(t)
                                 for t in np.array(ticklocs[axis])[valid]], rotation=90)

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
    max_width = None
    max_height = None
    min_width = None
    min_height = None
    font_family = None
    agro_mask_shp_file = None
    water_shp_file = None
    layers = None

    def __init__(self, **kwargs):
        self.points = {}
        self.cartopy_scale = '10m'

        self.xlim = None
        self.ylim = None

        if 'points' in kwargs:
            points.add_points(self, kwargs['points'])
            del kwargs['points']

        for k, v in kwargs.items():
            if k.startswith('_'):
                continue
            if hasattr(self, k):
                setattr(self, k, v)

    def _get_font_props(self, **kwargs):
        if self.font_family:
            if os.path.isfile(self.font_family):
                kwargs['fname'] = self.font_family
        return _fm.FontProperties(**kwargs)

    def add_point(self, lat: Number, lon: Number, text: str):
        self.points[(lon, lat)] = text

    def plot(self, file: DatasetReader, band=1):
        xlim, ylim = self._get_lims(file)
        plot_size = self._get_raster_size_inches(file)
        data = file.read(band)
        crs = self.get_projection(file)
        figsize = plot_size[0] + self.outer_size[1] + self.outer_size[3], plot_size[1] + self.outer_size[0] + self.outer_size[2]
        fig = pyplot.figure(figsize=figsize, dpi=self.dpi)

        # сконвертировать координаты изображения в пиксели (можно просто помножить на dpi)
        image_pos = self.outer_size[3], self.outer_size[0]  # позиция изображения в дюймах (от верхнего левого угла)
        image_pos_px = fig.dpi_scale_trans.transform((image_pos[0], figsize[1]-image_pos[1]-plot_size[1]))  # позиция изображеня в пикселях, от вернего левого угла
        image_pos_ax = fig.transFigure.inverted().transform(image_pos_px)  # в долях(?) (от 0 до 1)
        plot_size_ax = fig.transFigure.inverted().transform(fig.dpi_scale_trans.transform(plot_size))
        ax0 = fig.add_axes([0, 0, 1, 1])
        ax0.set_axis_off()
        # _plot_rect_with_outside_border(image_pos_ax, plot_size_ax, ax0)
        ax1 = fig.add_axes([*image_pos_ax, *plot_size_ax], projection=crs)
        self._build_figure(data, crs, ax1, xlim, ylim, file)
        plot_marks(self.points, crs, ax1)

        return fig, (ax0, ax1), plot_size

    def _build_figure(self, data, crs, ax1, xlim, ylim, file):
        build_figure(data, ax1, crs, cmap=self.cmap, norm=self.norm, xlim=xlim, ylim=ylim,
                     transform=file.transform,
                     water_shp_file=self.water_shp_file,
                     layers=self.layers)

    def _get_point_fontprops(self):
        return self._get_font_props(size=16)

    def plot_to_file(self, file: DatasetReader, output_file: str, band=1):
        figure, _1, _2 = self.plot(file, band)
        figure.savefig(output_file, bbox_inches=None, pad_inches=0, transparent=False)
        pyplot.close(figure)

    def get_projection(self, file):
        return CARTOPY_LCC

    def _get_lims(self, file: DatasetReader):
        xlim = self.xlim or (file.transform.c, file.transform.a * file.width + file.transform.c)
        ylim = self.ylim or (file.transform.e * file.height + file.transform.f, file.transform.f)
        return xlim, ylim

    def _get_raster_size_inches(self, file: DatasetReader):
        xlim, ylim = self._get_lims(file)
        plot_width = abs(xlim[0] - xlim[1]) / file.transform.a / self.dpi
        plot_height = abs(ylim[0] - ylim[1]) / file.transform.a / self.dpi
        zoom = 1

        if self.max_width is not None:
            zoom = min(zoom, self.max_width / plot_width)
        if self.min_width is not None:
            zoom = max(zoom, self.min_width / plot_width)
        if self.max_height is not None:
            zoom = min(zoom, self.max_height / plot_height)
        if self.min_height is not None:
            zoom = max(zoom, self.min_height / plot_height)
        plot_width *= zoom
        plot_height *= zoom
        return plot_width, plot_height





