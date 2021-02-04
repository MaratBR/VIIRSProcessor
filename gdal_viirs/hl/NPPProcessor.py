import inspect
import math
import os
import time
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path

from loguru import logger

from gdal_viirs.config import CONFIG, ConfigWrapper
from gdal_viirs.exceptions import ProcessingException
from gdal_viirs.maps import produce_image
from gdal_viirs.maps.ndvi_dynamics import NDVIDynamicsMapBuilder
from gdal_viirs.merge import merge_files2tiff
from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs import process as _process, utility as _utility
import gdal_viirs.hl.utility as _hlutil
from gdal_viirs.types import ViirsFileset


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
        for k in ('water_shapefile', 'mask_shapefile'):
            if k in entry and entry[k] is not None:
                if not isinstance(entry[k], str):
                    raise TypeError(f'парамент png_config[{i}]["{k}"] не является строкой или None')
                if not os.path.isfile(entry[k]):
                    logger.warning(f'файл указанный в конфигурации не найден: {entry[k]}')

        for k in ('xlim', 'ylim'):
            if 'name' not in entry or not isinstance(entry[k], (tuple, list)) or len(entry[k]) != 2:
                raise TypeError(f'обязательный параметр png_config[{i}]["{k}"] не является списком или кортежом с длинной 2')


def _validate_config(config):
    _validate_png_config(config['PNG_CONFIG'])


def _mkpath(p):
    p.mkdir(parents=True, exist_ok=True)
    return p


def _todaystr():
    return datetime.now().strftime('%Y%m%d')


class NPPProcessor:
    def __init__(self, config):
        logger.debug(f'config={config}')

        config = ConfigWrapper(CONFIG, config)
        _validate_config(config)
        config_dir = Path(os.path.expandvars(os.path.expanduser(config['CONFIG_DIR'])))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(config_dir / 'store.db'))

        self._processed_output = _mkpath(config.get_output('processed_data'))
        self._ndvi_output = _mkpath(config.get_output('ndvi'))
        self._ndvi_dynamics_output = _mkpath(config.get_output('ndvi_dynamics'))
        self._data_dir = _mkpath(config.get_input('data'))

        self.png_config = config['PNG_CONFIG']
        self._config = config

    def process_recent(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        for d in directories:
            if not os.path.isdir(d):
                continue
            try:
                logger.debug(f'проверка папки {d} ...')
                self._process_directory(d)
            except ProcessingException as e:
                logger.exception(e)

    def reset(self):
        self.persistence.reset()

    # region scale

    def _get_scale(self, band):
        scale = self._config.get(f'SCALE_BAND_{band}')
        if scale is None:
            raise ValueError(f'масштаб для канала {band} не найден')
        return scale

    # endregion

    # region вспомогательные функции

    def _fname(self, fs: _hlutil.NPPViirsFileset, kind, ext='tiff'):
        dir_path = _mkpath(self._processed_output / fs.geoloc_file.date.strftime('%Y%m%d') / fs.swath_id)
        base_name = fs.root_dir.parts[-1]
        return str(dir_path / (base_name + '.' + kind + '.' + ext))

    def _on_before_processing(self, name, src_type):
        logger.debug(f'обработка {src_type} @ {name}')

    def _on_after_processing(self, name, src_type):
        logger.debug(f'обработка завершена {src_type} @ {name}')

    def _on_exception(self, exc):
        logger.exception(exc)

    # endregion

    def _process_directory(self, d):
        filesets = _hlutil.find_npp_viirs_filesets(d)

        for fs in filesets:
            # обработка данных с level1
            l1_output_file = self._fname(fs, fs.geoloc_file.file_type_out)
            if not os.path.exists(l1_output_file):
                self._on_before_processing(l1_output_file, fs.geoloc_file.file_type)
                try:
                    _process.process_fileset(fs, l1_output_file, self._get_scale(fs.geoloc_file.band))
                except Exception as exc:
                    self._on_exception(exc)
                    raise
                self._on_after_processing(l1_output_file, fs.geoloc_file.file_type)

            handler_name = f'_process__{fs.geoloc_file.file_type.lower()}'
            if hasattr(self, handler_name):
                logger.debug(f'вызов обработчика {handler_name} ...')
                fn = getattr(self, handler_name)
                if hasattr(fn, '__call__'):
                    try:
                        fn(fs, l1_output_file)
                    except Exception as exc:
                        self._on_exception(exc)
                        raise
                else:
                    raise TypeError(f'обработчик {handler_name} найден, но не является функцией')

    def _process__gimgo(self, fs: _hlutil.NPPViirsFileset, processed_gimgo):
        root_dir = str(fs.root_dir)
        l2_input_file = glob(os.path.join(root_dir, 'viirs/level2/*CLOUDMASK.tif'))
        clouds_file = self._fname(fs, 'PROJECTED_CLOUDMASK')

        if not os.path.isfile(clouds_file):
            if len(l2_input_file) == 0:
                # если маска облачности еще не была посчитана для level2
                # мы не будем ничего делать и обработаем все потом
                logger.info(f'папка {root_dir} не содержит маски облачности в level2, дальнейшая обработка отложена до следующего запуска')
                return

            # перепроецируем маску облачности
            # все ошибки передаются в обработчик вызывающей функции
            _process.process_cloud_mask(l2_input_file[0], clouds_file, scale=self._get_scale('I'))

        # обработка NDVI
        self._process_ndvi_files(fs, clouds_file, processed_gimgo)

        # обработка ndvi изображений за последние N (5 по-умолчанию) дней
        merged = self._process_merged_ndvi_file_for_today()
        if merged is None:
            return
        merged, now, past_day = merged

        ndvi_dir = self._ndvi_output / _todaystr()
        if not ndvi_dir.is_dir():
            _mkpath(ndvi_dir)
        self._on_before_processing(str(ndvi_dir), 'ndvi_images')
        self._produce_ndvi_maps(merged, str(ndvi_dir),
                                date_text=now.strftime('%d.%m - ') + past_day.strftime('%d.%m.%Y'))
        self._on_after_processing(str(ndvi_dir), 'ndvi')

        # NDVI динамика
        ndvi_dynamics_dir = self._ndvi_dynamics_output / _todaystr()
        if not ndvi_dynamics_dir.is_dir():
            _mkpath(ndvi_dynamics_dir)
        # создать tiff c ndvi динамикой, если его нет
        ndvi_dynamics = self._process_ndvi_dynamics_for_today()
        if ndvi_dynamics is None:
            logger.warning('не удалось создать карты динамики развития посевов: недостаточно данных (композиты за последние 10 дней не найдены)')
        else:
            ndvi_dynamic_tiff, past_day, now = ndvi_dynamics
            _mkpath(ndvi_dynamics_dir)
            # создание карт динамики
            self._on_before_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')
            self._produce_ndvi_dynamics_maps(ndvi_dynamic_tiff, str(ndvi_dynamics_dir),
                                             date_text=now.strftime('%d.%m - ') + past_day.strftime('%d.%m.%Y'))
            self._on_after_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')

    def _process_ndvi_files(self, fs: _hlutil.NPPViirsFileset, clouds_file, gimgo_file):
        ndvi_file = self._fname(fs, 'NDVI')
        if not self.persistence.has_processed('ndvi', ndvi_file, strict=True):
            if os.path.isfile(gimgo_file):
                self._on_before_processing(ndvi_file, 'ndvi')
                _process.process_ndvi(gimgo_file, ndvi_file) # clouds_file
                self.persistence.add_ndvi(ndvi_file, fs.geoloc_file.date)
                self._on_after_processing(ndvi_file, 'ndvi')
                return ndvi_file
            else:
                logger.warning(f'не удалось найти файл {gimgo_file}, не могу обработать NDVI')
                raise ProcessingException(f'Файл GIMGO {gimgo_file} не найден')

    def _process_merged_ndvi_file_for_today(self):
        ndvi_rasters_bound_in_days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.combine(datetime.now().date(), datetime.min.time())
        past_day = now - timedelta(days=ndvi_rasters_bound_in_days)

        merged_ndvi_filename = 'merged_ndvi_' + now.strftime('%Y%m%d') + '_' + past_day.strftime('%Y%m%d') + '.tiff'
        output_file = _mkpath(self._processed_output / _todaystr() / 'daily') / merged_ndvi_filename

        if not self.persistence.has_processed('ndvi_composite', output_file, strict=True):
            ndvi_rasters = self.persistence.find_ndvi(past_day)
            if len(ndvi_rasters) == 0:
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                return None
            for raster in ndvi_rasters:
                if not os.path.isfile(raster):
                    logger.error(f'файл {raster} не найден, обнаружено несоотсветсвие БД')
            ndvi_rasters = list(filter(os.path.isfile, ndvi_rasters))
            self._on_before_processing(output_file, 'merged_ndvi')
            merge_files2tiff(ndvi_rasters, output_file, method='max')
            self.persistence.add_ndvi_composite(output_file, past_day.date(), now.date())
            self._on_after_processing(output_file, 'merged_ndvi')
        return output_file, now, past_day

    def _process_ndvi_dynamics_for_today(self):
        now = datetime.now().date()
        past_10days = now - timedelta(days=10)
        b2 = self.persistence.find_composite(ends_at=now)
        b1 = self.persistence.find_composite(starts_at=past_10days)

        if b1 is None:
            logger.warning(f'не удалось найти композит начинающийся с {past_10days} (b2)')
            return None
        if b2 is None:
            logger.error('не удалось найти композит, сделанный сегодня (b2)')
            return None

        filename = ''.join((
            f'ndvi_dynamics_',
            f'b1{b1.from_date.strftime("%Y%m%d")}-{b1.to_date.strftime("%Y%m%d")}',
            f'b2{b2.from_date.strftime("%Y%m%d")}-{b2.to_date.strftime("%Y%m%d")}',
        ))
        dynamics_tiff_output = _mkpath(self._processed_output / 'daily') / filename

        if not dynamics_tiff_output.is_file():
            self._on_before_processing(str(dynamics_tiff_output), 'ndvi_dynamics')
            _process.process_ndvi_dynamics(b1, b2, str(dynamics_tiff_output))
            self._on_after_processing(str(dynamics_tiff_output), 'ndvi_dynamics')
        return str(dynamics_tiff_output), past_10days, now

    def _produce_ndvi_dynamics_maps(self, ndvi_dynamics_input: str, output_dir: str, date_text=None):
        self._produce_images(ndvi_dynamics_input, output_dir, date_text, builder=NDVIDynamicsMapBuilder)

    def _produce_ndvi_maps(self, merged_ndvi: str, png_dir: str, date_text=None):
        self._produce_images(merged_ndvi, png_dir, date_text)

    def _produce_images(self, input_file, output_directory, date_text=None, builder=None):
        png_config = self._config.get("PNG_CONFIG")
        for index, png_entry in enumerate(png_config):
            name = png_entry['name']
            filename = f'{name}.png'
            filepath = os.path.join(output_directory, filename)
            if os.path.isfile(filepath):
                continue
            display_name = png_entry.get('display_name')
            xlim = png_entry.get('xlim')
            ylim = png_entry.get('ylim')
            props = {
                'bottom_subtitle': display_name,
                'map_points': self._config.get('MAP_POINTS'),
                'date_text': date_text
            }
            if 'FONT_FAMILY' in self._config:
                props['font_family'] = self._config['FONT_FAMILY']
            if xlim:
                props['xlim'] = xlim
            if ylim:
                props['ylim'] = ylim
            props['water_shp_file'] = png_entry.get('water_shapefile')
            props['points'] = png_entry.get('points')
            shapefile = png_entry.get('mask_shapefile')
            if shapefile is None:
                logger.warning(f'изображение с идентификатором {name} (png_config[{index}]) не имеет mask_shapefile')

            logger.debug(f'обработка изображения ({index + 1}/{len(png_config)}) {filepath}')
            produce_image(input_file, filepath,
                          builder=builder,
                          logo_path=self._config['LOGO_PATH'],
                          iso_sign_path=self._config['ISO_QUALITY_SIGN'],
                          shp_mask_file=shapefile, **props)






