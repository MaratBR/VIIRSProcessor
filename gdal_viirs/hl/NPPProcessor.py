import math
import os
import time
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path

from loguru import logger

from gdal_viirs._config import CONFIG
from gdal_viirs.exceptions import ProcessingException
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


def _validate_config(config):
    _validate_png_config(config['PNG_CONFIG'])


class NPPProcessor:
    def __init__(self, config: dict):
        config = {
            **CONFIG,
            **config
        }
        logger.debug(f'config={config}')
        _validate_config(config)
        config_dir = Path(os.path.expandvars(os.path.expanduser(config['CONFIG_DIR'])))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(config_dir / 'store.db'))
        self._output_dir = os.path.expandvars(os.path.expanduser(config['OUTPUT_DIR']))
        self._data_dir = os.path.expandvars(os.path.expanduser(config['INPUT_DIR']))
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        self.scale = config['SCALE']
        self.png_config = config['PNG_CONFIG']
        self._config = config

    def _fname(self, d, kind, ext='tiff'):
        return os.path.join(self._output_dir, os.path.basename(d) + '.' + kind + '.' + ext)

    def process_recent(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        for d in directories:
            if not os.path.isdir(d):
                continue
            try:
                self._process_directory(d)
            except ProcessingException as e:
                logger.exception(e)

    def reset(self):
        self.persistence.delete_meta('last_check_time')
        self.persistence.reset()

    def _process_directory(self, d):
        logger.debug('level1')
        products = self._produce_level1_products(d)

        if 'l1_GIMGO' not in products:
            raise ProcessingException('Не удалось обработать или найти уже обработанный GIMGO файл в БД')
        else:
            logger.debug('cloud_mask')
            clouds_file = self._process_clouds_file(d)
            if clouds_file is None:
                logger.warning(f'Маска облачности для папки {d} не была обработана: маска облачность в level2 еще не сгенерирована')
            else:
                logger.debug('ndvi')
                self._process_ndvi_files(d, clouds_file)

                logger.debug('merged_ndvi')
                merged_ndvi, now, past = self._process_merged_ndvi_file_for_today()

                logger.debug('png\'s')
                png_dir = os.path.join(self._output_dir, datetime.now().strftime('PNG.%Y_%b_%d'))
                Path(png_dir).mkdir(parents=True, exist_ok=True)

                png_config = self.png_config
                self._produce_pngs(merged_ndvi, png_config, png_dir,
                                   bottom_right_text=now.strftime('%Y.%m.%d') + ' - ' + past.strftime('%Y.%m.%d'))

    def _produce_level1_products(self, d):
        products = {}
        filesets = _utility.find_sdr_viirs_filesets(os.path.join(d, 'viirs/level1')).values()
        for fs in filesets:
            type_ = 'l1_' + fs.geoloc_file.file_type
            logger.debug(type_)
            if self.persistence.has_processed(d, type_, strict=True):
                products[type_] = self.persistence.get_processed(d, type_)
                continue
            fs.geoloc_file.date.strftime('')
            output_file = self._fname(d, fs.geoloc_file.file_type_out)
            _process.process_fileset(fs, output_file, self.scale)
            self.persistence.add_processed(d, type_, output_file)
            products[type_] = output_file
        return products

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
            gimgo_tiff_file = self._fname(d, 'VIMGO')
            if os.path.isfile(gimgo_tiff_file):
                _process.process_ndvi(gimgo_tiff_file, ndvi_file, clouds_file)
                self.persistence.add_processed(d, 'ndvi', ndvi_file)
                return ndvi_file
            else:
                logger.warning(f'не удалось найти файл {gimgo_tiff_file}, не могу обработать NDVI')
                raise ProcessingException(f'Файл GIMGO {gimgo_tiff_file} не найден')

    def _process_merged_ndvi_file_for_today(self):
        ndvi_rasters_bound_in_days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.now().date()
        past_day = now - timedelta(days=ndvi_rasters_bound_in_days)
        merged_ndvi = 'NDVI_' + now.strftime('%Y_%b_%d') + '-' + past_day.strftime('%Y_%b_%d')
        merged_ndvi_file = merged_ndvi + '.tiff'
        output_file = os.path.join(self._output_dir, merged_ndvi_file)
        if not self.persistence.has_processed(merged_ndvi, '', strict=True):
            ndvi_rasters = self.persistence.find_processed('created_at_ts >= ? AND type = ?',
                                                           [math.floor(time.mktime(past_day.timetuple())), 'ndvi'])
            if len(ndvi_rasters) == 0:
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                return None
            for raster in ndvi_rasters:
                if not os.path.isfile(raster):
                    raise ProcessingException(f'файл {raster} не найден, обнаружено несоотсветсвие БД')
            merge_files2tiff(ndvi_rasters, output_file)
            self.persistence.add_processed(merged_ndvi, '', output_file)
        return output_file, now, past_day

    def _produce_pngs(self, merged_ndvi: str, png_config: list, png_dir: str, category_name=None,
                      bottom_right_text=None):
        for index, png_entry in enumerate(png_config):
            name = png_entry['name']
            display_name = png_entry.get('display_name')
            xlim = png_entry.get('xlim')
            ylim = png_entry.get('ylim')
            filename = f'{name}.{category_name}.png' if category_name else f'{name}.png'
            filepath = os.path.join(png_dir, filename)
            props = {
                'bottom_subtitle': display_name,
                'map_points': self._config.get('MAP_POINTS'),
                'bottom_right_text': bottom_right_text
            }
            if 'FONT_FAMILY' in self._config:
                props['font_family'] = self._config['FONT_FAMILY']
            if xlim:
                props['xlim'] = xlim
            if ylim:
                props['ylim'] = ylim
            shapefile = png_entry.get('mask_shapefile')
            if shapefile is None:
                logger.warning(f'изображение с идентификатором {name} (png_config[{index}]) не имеет mask_shapefile')
            produce_ndvi_image(merged_ndvi, filepath,
                               logo_path=self._config['LOGO_PATH'],
                               iso_sign_path=self._config['ISO_QUALITY_SIGN'],
                               shp_mask_file=shapefile, **props)






