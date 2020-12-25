import rasterio.plot

from gdal_viirs.types import Number
from typing import Tuple, Optional
from rasterio import DatasetReader
from matplotlib import pyplot
import cartopy

_CM = 1/2.54

def cm(v):
    return v * _CM


def build_figure(data, image_size: Tuple[Number, Number], crs: cartopy.crs.Projection, *, xlim: Tuple[Number, Number] = None,
                 ylim: Tuple[Number, Number] = None, scale='10m', cmap=None, norm=None, transform=None):
    figure, axes = pyplot.subplots(figsize=image_size, projection=crs)
    axes.set_axis_off()
    if xlim:
        axes.set_xlim(xlim)
    if ylim:
        axes.set_ylim(ylim)

    coastline = cartopy.feature.NaturalEarthFeature(category='physical',
                                                    name='coastline',
                                                    scale=scale,
                                                    facecolor='None')
    minor_islands = cartopy.feature.NaturalEarthFeature(category='physical',
                                                        name='minor_islands',
                                                        scale=scale,
                                                        facecolor='None')
    lakes_contour = cartopy.feature.NaturalEarthFeature(category='physical',
                                                        name='lakes',
                                                        scale=scale,
                                                        facecolor='None')
    admin_0_countries = cartopy.feature.NaturalEarthFeature(category='cultural',
                                                            name='admin_0_countries',
                                                            scale=scale,
                                                            facecolor='None')
    admin_1_states_provinces = cartopy.feature.NaturalEarthFeature(category='cultural',
                                                                   name='admin_1_states_provinces',
                                                                   scale=scale,
                                                                   facecolor='None')

    rasterio.plot.show(data, cmap=cmap, norm=norm, ax=axes, transform=transform, origin='upper',
                       interpolation='nearest')

    axes.add_feature(coastline, edgecolor='black', linewidth=2)
    axes.add_feature(minor_islands, edgecolor='black', linewidth=0.5)
    axes.add_feature(lakes_contour, edgecolor='black', linewidth=0.4)
    axes.add_feature(admin_0_countries, edgecolor='black', linewidth=3)
    axes.add_feature(admin_1_states_provinces, edgecolor='black', linewidth=1)

    return figure, axes


class MapBuilder:
    xlim: Optional[Tuple[Number, Number]]
    ylim: Optional[Tuple[Number, Number]]
    cartopy_scale: str
    plot_size: Tuple[Number, Number]
    cmap = None
    norm = None
    marks_color = 'blue'
    font_size = 25

    def __init__(self):
        self._points = {}
        self.xlim = None
        self.ylim = None
        self.cartopy_scale = '10m'
        self.plot_size = cm(30), cm(30)

    def add_point(self, lon: Number, lat: Number, text: str):
        self._points[(lat, lon)] = text

    def plot(self, file: DatasetReader, band=1):
        data = file.read(band)
        crs = self.get_projection(file)
        fig, axes = build_figure(data, self.plot_size, cmap=self.cmap, norm=self.norm, xlim=self.xlim, ylim=self.ylim,
                            crs=crs)

        geod = cartopy.crs.Geodetic()
        plate_carree = cartopy.crs.PlateCarree()
        for coord, text in self._points.items():
            axes.plot(*coord, color=self.marks_color, markersize=22, marker='o', transform=geod)
            point = crs.transform_point(coord[0], coord[1], plate_carree)
            axes.text(point[0] + 25, point[1] + 25, 'Новосибирск', color=self.marks_color, fontdict={
                'family': 'serif',
                'weight': 'normal',
                'size': 40,
            })

        return fig, axes

    def plot_to_file(self, file: DatasetReader, output_file: str, band=1):
        figure, _ = self.plot(file, band)
        figure.savefig(output_file, bbox_inches='tight', pad_inches=0, transparent=False)

    def get_projection(self, file):
        return cartopy.crs.PlateCarree()




