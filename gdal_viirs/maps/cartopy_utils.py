from cartopy.crs import PlateCarree
import numpy as np

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
