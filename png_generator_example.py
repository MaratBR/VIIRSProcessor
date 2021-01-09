import rasterio
from gdal_viirs.maps.ndvi import NDVIMapBuilder

b = NDVIMapBuilder(font_family='/home/marat/Downloads/Agro/Font/times.ttf')
with rasterio.open('/home/marat/Documents/NPP_47498_27-DEC-2020_073021.NDVI.tiff') as f:
    b.plot_to_file(f, '/home/marat/Documents/NPP_47498_27-DEC-2020_073021.NDVI_IMG.png')