import math
import os
import time
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path

from loguru import logger

from gdal_viirs.maps import produce_ndvi_image
from gdal_viirs.merge import merge_files2tiff
from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs import process as _process, utility as _utility


def _validate_png_config(png_config):
    if not isinstance(png_config, (list, set, tuple)):
        raise TypeError('png_config может быть только списком (list), сетом (set) или котрежом (tuple)')

    for i, entry in enumerate(png_config):
        if not isinstance(entry, dict):
            raise TypeError(f'элемент png_config[{i}] не является словарём')
        if 'name' not in entry or not isinstance(entry['name'], str):
            raise TypeError(f'png_config[{i}]["name"] не является строкой или отсутсвует')
        if 'display_name' in entry and entry['display_name'] is not None and not isinstance(entry['display_name'], str):
            raise TypeError(f'png_config[{i}]["display_name"] не является строкой или None')
        for k in ('xlim', 'ylim'):
            if 'name' not in entry or not isinstance(entry[k], (tuple, list)) or len(entry[k]) != 2:
                raise TypeError(f'обязательный параметр png_config[{i}]["{k}"] не является списком или кортежом с длинной 2')


class NPPProcessor:
    def __init__(self, data_dir: str, output_dir: str, config_dir='~/.viirs_processor', scale=2000, png_config=None, **kwargs):
        config_dir = Path(os.path.expandvars(os.path.expanduser(config_dir)))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(config_dir / 'store.db'))
        self._output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        self._data_dir = os.path.expandvars(os.path.expanduser(data_dir))
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        self.scale = scale
        _validate_png_config(png_config)
        self.png_config = png_config
        self._config = kwargs

    def _fname(self, d, kind, ext='tiff'):
        return os.path.join(self._output_dir, os.path.basename(d) + '.' + kind + '.' + ext)

    def process_recent(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        for d in directories:
            if not os.path.isdir(d):
                continue
            self._process_directory(d)

    def reset(self):
        self.persistence.delete_meta('last_check_time')
        self.persistence.reset()

    def _process_directory(self, d):
        dirname = os.path.basename(d)
        logger.debug('level1')
        if not self.persistence.has_processed(d, 'level1', strict=True):
            filesets = _utility.find_sdr_viirs_filesets(os.path.join(d, 'viirs/level1')).values()
            for fs in filesets:
                fs.geoloc_file.date.strftime('')
                output_file = self._fname(dirname, fs.geoloc_file.file_type)
                _process.process_fileset(fs, output_file, self.scale)
            self.persistence.add_processed(d, 'level1', output_file)

        logger.debug('cloud_mask')
        clouds_file = self._process_clouds_file(d)
        if clouds_file is None:
            return
        logger.debug('ndvi')
        self._process_ndvi_files(d, clouds_file)
        logger.debug('merged_ndvi')
        try:
            merged_ndvi = self._process_merged_ndvi_file()
        except FileNotFoundError as e:
            logger.error(str(e))
            return

        logger.debug('png\'s')
        png_config = self.png_config
        png_dir = os.path.join(self._output_dir, datetime.now().strftime('PNG.%Y_%b_%d'))
        Path(png_dir).mkdir(parents=True, exist_ok=True)
        self._produce_pngs(merged_ndvi, png_config, png_dir)

    def _process_clouds_file(self, d):
        clouds_file = self._fname(d, 'PROJECTED_CLOUDMASK')
        if not self.persistence.has_processed(d, 'cloud_mask', strict=True):
            input_file = glob(os.path.join(d, 'viirs/level2/*CLOUDMASK.tif'))
            if len(input_file) != 0:
                input_file = input_file[0]
                _process.process_cloud_mask(input_file, clouds_file, scale=self.scale)
                self.persistence.add_processed(d, 'cloud_mask', clouds_file)
            else:
                return None
        return clouds_file

    def _process_ndvi_files(self, d, clouds_file):
        if self.persistence.has_processed(d, 'cloud_mask', strict=True) and not self.persistence.has_processed(d, 'ndvi', strict=True):
            ndvi_file = self._fname(d, 'NDVI')
            gimgo_tiff_file = self._fname(d, 'GIMGO')
            if os.path.isfile(gimgo_tiff_file):
                _process.process_ndvi(gimgo_tiff_file, ndvi_file, clouds_file)
                self.persistence.add_processed(d, 'ndvi', ndvi_file)
                return ndvi_file
            else:
                logger.warning(f'не удалось найти файл {gimgo_tiff_file}, не могу обработать NDVI')

    def _process_merged_ndvi_file(self):
        ndvi_rasters_bound_in_days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.now().date()
        past_day = now - timedelta(days=ndvi_rasters_bound_in_days)
        merged_ndvi = 'NDVI_' + now.strftime('%Y_%b_%d') + '-' + past_day.strftime('%Y_%b_%d')
        merged_ndvi_file = merged_ndvi + '.tiff'
        output_file = os.path.join(self._output_dir, merged_ndvi_file)
        if not self.persistence.has_processed(merged_ndvi, '', strict=True):
            ndvi_rasters = self.persistence.get_processed('created_at_ts >= ? AND type = ?',
                                                          [math.floor(time.mktime(past_day.timetuple())), 'ndvi'])
            if len(ndvi_rasters) == 0:
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                return None
            for raster in ndvi_rasters:
                if not os.path.isfile(raster):
                    raise FileNotFoundError(f'файл {raster} не найден, обнаружено несоотсветсвие БД')
            merge_files2tiff(ndvi_rasters, output_file)
            self.persistence.add_processed(merged_ndvi, '', output_file)
        return output_file

    def _produce_pngs(self, merged_ndvi: str, png_config: list, png_dir: str, category_name=None):
        for index, png_entry in enumerate(png_config):
            name = png_entry['name']
            display_name = png_entry.get('display_name')
            xlim = png_entry.get('xlim')
            ylim = png_entry.get('ylim')
            filename = f'{name}.{category_name}.png' if category_name else f'{name}.png'
            filepath = os.path.join(png_dir, filename)
            props = dict(bottom_subtitle=display_name, map_points=self._config.get('map_points'),
                         )
            if xlim:
                props['xlim'] = xlim
            if ylim:
                props['ylim'] = ylim
            shapefile = png_entry.get('mask_shapefile')
            if shapefile is None:
                logger.warning(f'изображение с идентификатором {name} (png_config[{index}]) не имеет mask_shapefile')
            produce_ndvi_image(merged_ndvi, filepath, shp_mask_file=shapefile, **props)






