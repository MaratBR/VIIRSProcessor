import rasterio

from gdal_viirs.maps.novosibirsk import *
b = NovosibirskMapBuilder()

with rasterio.open('/home/marat/Downloads/ndvi (6).tiff') as f:
    b.cmap = 'Reds'
    b.plot_to_file(f, '/home/marat/Documents/out.png')
