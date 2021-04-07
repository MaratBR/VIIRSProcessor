import cartopy
import numpy as np
from cartopy.crs import PlateCarree


def get_lonlat_lim_range(extent, crs):
    pc = PlateCarree()
    xmin, xmax, ymin, ymax = extent
    x = np.array([
        xmin,
        xmin,
        xmax,
        xmax
    ])
    y = np.array([
        ymin,
        ymax,
        ymin,
        ymax
    ])
    points = pc.transform_points(crs, x, y)
    lon = points[:, 0]
    lat = points[:, 1]
    return (lon.min(), lon.max()), (lat.min(), lat.max())


CARTOPY_LCC = cartopy.crs.LambertConformal(
    standard_parallels=(43.58046825, 67.41206675),
    central_longitude=79.950619,
    central_latitude=55.4962675
)
