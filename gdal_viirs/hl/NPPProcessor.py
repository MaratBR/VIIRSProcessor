import os
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from typing import List

import peewee
from loguru import logger

from gdal_viirs.config import CONFIG, ConfigWrapper
from gdal_viirs.exceptions import ProcessingException
from gdal_viirs.maps import produce_image
from gdal_viirs.maps.ndvi_dynamics import NDVIDynamicsMapBuilder
from gdal_viirs.merge import merge_files2tiff
from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs.persistence.models import *
from gdal_viirs import process as _process
import gdal_viirs.hl.utility as _hlutil


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
                raise TypeError(
                    f'обязательный параметр png_config[{i}]["{k}"] не является списком или кортежом с длинной 2')


def _check_config_values(config):
    if config['SCALE_BAND_I'] != CONFIG['SCALE_BAND_I']:
        logger.warning(f'SCALE_BAND_I = {config["SCALE_BAND_I"]}')
    if config['SCALE_BAND_M'] != CONFIG['SCALE_BAND_M']:
        logger.warning(f'SCALE_BAND_M = {config["SCALE_BAND_M"]}')
    if config['SCALE_BAND_I'] != CONFIG['SCALE_BAND_I']:
        logger.warning(f'SCALE_BAND_DN = {config["SCALE_BAND_DN"]}')

    if 'SCALE_MULTIPLIER' in config:
        if config['SCALE_MULTIPLIER'] < 1:
            logger.warning('коэфициент масштаба (SCALE_MULTIPLIER в конфигурации) меньше 1 и будет проигнорирован')
        elif config['SCALE_MULTIPLIER'] > 1:
            multiplier = config['SCALE_MULTIPLIER']
            logger.warning(f'коэфициент масштаба установлен {multiplier}, масштаб будет '
                           f'{round(config["SCALE_BAND_I"] * multiplier)}, {round(config["SCALE_BAND_M"] * multiplier)}'
                           f', {round(config["SCALE_BAND_DN"] * multiplier)} для I, M и DN каналов соответственно')


def _validate_config(config):
    _validate_png_config(config['PNG_CONFIG'])
    _check_config_values(config)


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

        # db
        self._db = peewee.SqliteDatabase(str(config_dir / 'viirs_processor.db'))
        db_proxy.initialize(self._db)
        self._db.create_tables(PEEWEE_MODELS)

    def _find_viirs_directories(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        directories = list(filter(os.path.isdir, directories))
        logger.debug(f'Найдено {len(directories)} папок с данными')
        return directories

    def process_recent(self):
        for d in self._find_viirs_directories():
            try:
                logger.debug(f'проверка папки {d} ...')
                self._process_directory(d)
            except ProcessingException as e:
                logger.exception(e)

        self._produce_daily_products()

    # region вспомогательные функции

    def _get_scale(self, band):
        scale = self._config.get(f'SCALE_BAND_{band}')
        if scale is None:
            raise ValueError(f'масштаб для канала {band} не найден')
        if 'SCALE_MULTIPLIER' in self._config:
            scale *= max(1, self._config['SCALE_MULTIPLIER'])
        scale = round(scale)
        return scale

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

    def _process_directory(self, input_directory):
        filesets = _hlutil.find_npp_viirs_filesets(input_directory)
        if len(filesets) == 0:
            logger.warning(f'не найдено ни одного датасета в папке {input_directory}')
        logger.debug(f'найдено {len(filesets)} в папке {input_directory}')

        for fs in filesets:
            # обработка данных с level1
            l1_output_file = _mkpath(self._processed_output / fs.geoloc_file.date.strftime('%Y%m%d') / fs.swath_id) \
                             / f'{fs.root_dir.parts[-1]}'
            if not l1_output_file.is_file():
                self._on_before_processing(str(l1_output_file), fs.geoloc_file.file_type)
                try:
                    _process.process_fileset(fs, str(l1_output_file), self._get_scale(fs.geoloc_file.band))
                except Exception as exc:
                    self._on_exception(exc)
                    raise

                self._on_after_processing(str(l1_output_file), fs.geoloc_file.file_type)

            processed: ProcessedViirsL1 = ProcessedViirsL1.get_or_none(ProcessedViirsL1.output_file == l1_output_file)
            if processed is None:
                # сохранить данные в БД
                processed = ProcessedViirsL1(l1_output_file, fs.geoloc_file.date,
                                             geoloc_filename=fs.geoloc_file.path_obj.parts[-1],
                                             type=fs.geoloc_file.file_type,
                                             input_directory=input_directory)
                processed.save(True)

            handler_name = f'_process__{fs.geoloc_file.file_type.lower()}'
            if hasattr(self, handler_name):
                logger.debug(f'вызов обработчика {handler_name} ...')
                fn = getattr(self, handler_name)
                if hasattr(fn, '__call__'):
                    try:
                        fn(processed)
                    except Exception as exc:
                        self._on_exception(exc)
                        raise
                else:
                    raise TypeError(f'обработчик {handler_name} найден, но не является функцией')

    def _process__gimgo(self, processed: ProcessedViirsL1):
        try:
            clouds_file = self._process_cloud_mask(processed)
        except ProcessingException:
            return
        # обработка NDVI
        self._process_ndvi_files(processed, clouds_file)

    def _produce_daily_products(self):
        logger.info('обработка ежедневных продуктов...')
        self._produce_merged_ndvi_file_for_today()
        self._process_ndvi_dynamics_for_today()

    def _produce_maps(self):
        self._produce_ndvi_maps()
        self._produce_ndvi_dynamics_maps()

    def _produce_ndvi_dynamics_maps(self, day=None):
        if self._config.get('UPDATE_DYNAMICS_WHEN_MAKING_MAPS', False):
            day = day or datetime.now().date()
            ndvi_dynamics = NDVIDynamicsTiff.select() \
                .join(NDVIComposite, on=(NDVIComposite.id == NDVIDynamicsTiff.b2_composite))\
                .where(NDVIComposite.ends_at == day)
            ndvi_dynamics = list(ndvi_dynamics)
            if len(ndvi_dynamics):
                logger.warning('не удалось найти не одной записи о NDVI динамики, которая бы заканчивалась'
                               f' {day}, не могу создать карты динамики NDVI')
                return

        ndvi_dynamics = self._process_ndvi_dynamics_for_today()
        ndvi_dynamics_dir = self._ndvi_dynamics_output / _todaystr()
        _mkpath(ndvi_dynamics_dir)
        # создание карт динамики
        self._on_before_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')
        date_text = ndvi_dynamics.b1_composite.starts_at.strftime('%d.%m - ') + ndvi_dynamics.b1_composite.ends_at.strftime('%d.%m.%Y')
        self._produce_images(ndvi_dynamics.output_file, str(ndvi_dynamics_dir),
                             date_text=date_text, builder=NDVIDynamicsMapBuilder)

        self._on_after_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')

    # region ndvi / ndvi dynamics

    def _process_cloud_mask(self, processed: ProcessedViirsL1) -> Path:
        level2_folder = os.path.join(processed.input_directory, 'viirs/level2')
        l2_input_file = glob(os.path.join(level2_folder, '*CLOUDMASK.tif'))
        clouds_file = _mkpath(self._processed_output / _todaystr()) / f'{processed.directory_name}.PROJECTED_CLOUDMASK.tiff'

        if not os.path.isfile(clouds_file) or self._config.get('FORCE_CLOUD_MASK_PROCESSING', False):
            if len(l2_input_file) == 0:
                # если маска облачности еще не была посчитана для level2
                # мы не будем ничего делать и обработаем все потом
                logger.info(f'папка {processed.input_directory} не содержит маски облачности '
                            f'в level2, дальнейшая обработка отложена до следующего запуска')
                raise ProcessingException('не удалось обработать маску облачности: исходный файл не найден')

            # перепроецируем маску облачности
            # все ошибки передаются в обработчик вызывающей функции
            self._on_before_processing(clouds_file, 'clouds_file')
            _process.process_cloud_mask(l2_input_file[0], clouds_file, scale=self._get_scale('I'))
            self._on_after_processing(clouds_file, 'clouds_file')
        else:
            logger.debug('пропускаем cloud_file @ ' + str(clouds_file))

        return clouds_file

    def _process_ndvi_files(self, based_on: ProcessedViirsL1, clouds_file) -> NDVITiff:
        assert based_on.type == 'GIMGO'
        ndvi_file = _mkpath(
            self._processed_output / based_on.dataset_date.strftime('%Y%m%d') / based_on.swath_id
        ) / f'{based_on.directory_name}.NDVI.tiff'

        ndvi_record: NDVITiff = NDVITiff.get_or_none(NDVITiff.based_on == based_on)

        if not os.path.isfile(ndvi_file):
            if os.path.isfile(based_on.output_file):
                self._on_before_processing(ndvi_file, 'ndvi')
                _process.process_ndvi(based_on.output_file, ndvi_file, clouds_file)

                # сохраняем запись с БД
                tiff_record = NDVITiff(ndvi_file)
                tiff_record.based_on = based_on
                tiff_record.save(True)
                self._on_after_processing(ndvi_file, 'ndvi')
                return ndvi_file
            else:
                logger.warning(f'не удалось найти файл {based_on.output_file}, не могу обработать NDVI')
                raise ProcessingException(f'Файл GIMGO {based_on.output_file} не найден')
        else:
            logger.debug('пропускаем ndvi @ ' + str(ndvi_file))

        if ndvi_record is None:
            ndvi_record = NDVITiff(ndvi_file, based_on=based_on)
            ndvi_record.save(True)
        elif ndvi_record.output_file != ndvi_file:
            ndvi_record.update({
                NDVITiff.output_file: ndvi_file
            })
        return ndvi_record

    def _produce_merged_ndvi_file_for_today(self) -> NDVIComposite:
        """
        Обрабатывает композит для сегодняшнего дня

        :raises: ProcessingException - если не найден ни один NDVI tiff
        :return: NDVIComposite
        """
        ndvi_rasters_bound_in_days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.combine(datetime.now().date(), datetime.min.time())
        past_day = now - timedelta(days=ndvi_rasters_bound_in_days)

        merged_ndvi_filename = 'merged_ndvi_' + now.strftime('%Y%m%d') + '_' + past_day.strftime('%Y%m%d') + '.tiff'
        output_file = _mkpath(self._processed_output / _todaystr() / 'daily') / merged_ndvi_filename

        if not os.path.isfile(merged_ndvi_filename) or self._config.get('FORCE_NDVI_COMPOSITE_PROCESSING', True):
            ndvi_records = NDVITiff.select()\
                .join(ProcessedViirsL1)\
                .where((ProcessedViirsL1.dataset_date <= now) & (ProcessedViirsL1.dataset_date >= past_day))
            ndvi_records: List[NDVITiff] = list(ndvi_records)

            # если не одного NDVI tiff'а не найдено, выбросить исключение
            if len(ndvi_records) == 0:
                no_ndvi_count = ProcessedViirsL1.select_gimgo_without_ndvi().count()
                if no_ndvi_count > 0:
                    logger.warning(f'найдено {no_ndvi_count} обработанных GIMGO снимков, '
                                   f'которые не имеют соответствующих NDVI')
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                raise ProcessingException('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')

            for raster in ndvi_records:
                if not os.path.isfile(raster.output_file):
                    logger.error(f'файл {raster} не найден, обнаружено несоотсветсвие БД')
            ndvi_rasters = list(filter(lambda r: os.path.isfile(r.output_file), ndvi_records))
            ndvi_rasters = list(map(lambda r: r.output_file, ndvi_rasters))
            self._on_before_processing(output_file, 'merged_ndvi')
            merge_files2tiff(ndvi_rasters, output_file, method='max')
            self._on_after_processing(output_file, 'merged_ndvi')

        composite = NDVIComposite.get_or_none(NDVIComposite.output_file == str(output_file))

        if composite is None:
            composite = NDVIComposite(output_file, starts_at=past_day, ends_at=now)
            composite.save(True)

        return composite

    # endregion

    # region maps

    def _produce_ndvi_maps(self):
        merged_ndvi = self._produce_merged_ndvi_file_for_today()
        png_dir = str(_mkpath(self._ndvi_output / _todaystr()))
        date_text = merged_ndvi.ends_at.strftime('%d.%m - ') + merged_ndvi.starts_at.strftime('%d.%m.%Y')
        self._produce_images(merged_ndvi.output_file, png_dir, date_text)

    def _process_ndvi_dynamics_for_today(self):
        now = datetime.now().date()
        ndvi_dynamics_period_in_days = self._config.get(
            'NDVI_DYNAMICS_PERIOD',
            self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5) * 2
        )
        past_days = now - timedelta(days=ndvi_dynamics_period_in_days)
        b2: NDVIComposite = NDVIComposite.get_or_none(NDVIComposite.ends_at == now)
        b1: NDVIComposite = NDVIComposite.get_or_none(NDVIComposite.starts_at == past_days)

        if b1 is None:
            logger.warning(f'не удалось найти композит начинающийся с {past_days} (b1)')
            return None
        if b2 is None:
            logger.error(f'не удалось найти композит, сделанный сегодня (b2, now={now})')
            return None

        filename = ''.join((
            f'ndvi_dynamics_',
            f'b1{b1.from_date.strftime("%Y%m%d")}-{b1.to_date.strftime("%Y%m%d")}',
            f'b2{b2.from_date.strftime("%Y%m%d")}-{b2.to_date.strftime("%Y%m%d")}',
        ))
        dynamics_tiff_output = _mkpath(self._processed_output / 'daily') / filename

        if not dynamics_tiff_output.is_file() or self._config.get('FORCE_NDVI_DYNAMICS_PROCESSING', True):
            self._on_before_processing(str(dynamics_tiff_output), 'ndvi_dynamics')
            _process.process_ndvi_dynamics(b1.output_file, b2.output_file, str(dynamics_tiff_output))
            self._on_after_processing(str(dynamics_tiff_output), 'ndvi_dynamics')

        record: NDVIDynamicsTiff = NDVIDynamicsTiff.get_or_none((NDVIDynamicsTiff.b1_composite == b1) & (NDVIDynamicsTiff.b2_composite == b2))
        if record is None:
            record = NDVIDynamicsTiff(dynamics_tiff_output)
            record.b1_composite = b1
            record.b2_composite = b2
            record.save(True)
        elif record.output_file != dynamics_tiff_output:
            record.update({
                NDVIDynamicsTiff.output_file: dynamics_tiff_output
            })

        return record

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

    # endregion
