import fiona
import rasterio
from rasterio.mask import mask

from gdal_viirs.maps.ndvi import NDVIMapBuilder


def produce_image(ndvi_file, output_file, shp_mask_file=None, builder=None, **kwargs):
    builder_instance = (builder or NDVIMapBuilder)(**kwargs)
    if shp_mask_file:
        # прочитать данные маски и применить её
        with fiona.open(shp_mask_file) as shp_file:
            geoms = [feature["geometry"] for feature in shp_file]
        with rasterio.open(ndvi_file) as input_file:
            out_image, out_transform = mask(input_file, geoms, all_touched=True)
            meta = input_file.meta.copy()

        with rasterio.MemoryFile() as memf:
            meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            with memf.open(**meta) as new_file:
                new_file.write(out_image)
                builder_instance.plot_to_file(new_file, output_file)
    else:
        with rasterio.open(ndvi_file) as f:
            builder_instance.plot_to_file(f, output_file)
