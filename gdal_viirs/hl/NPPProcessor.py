import os
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path
from typing import List, Optional

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
        config = ConfigWrapper(CONFIG, config)
        _validate_config(config)
        logger.debug(f'config={config}')
        config_dir = Path(os.path.expandvars(os.path.expanduser(config['CONFIG_DIR'])))
        config_dir.mkdir(parents=True, exist_ok=True)
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
        self._on_start()
        self.produce_products()
        self._produce_maps()

    def produce_maps(self):
        self._on_start()
        self._produce_maps()

    def produce_products(self):
        self._on_start()
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

    def _on_before_processing(self, name, src_type):
        logger.debug(f'обработка {src_type} @ {name}')

    def _on_after_processing(self, name, src_type):
        logger.debug(f'обработка завершена {src_type} @ {name}')

    def _on_exception(self, exc):
        logger.exception(exc)

    def _on_start(self):
        if hasattr(self, '_on_start_fired'):
            return
        setattr(self, '_on_start_fired', True)
        MetaData.set_meta('last_start', str(datetime.now()))

    # endregion

    def _process_directory(self, input_directory):
        filesets = _hlutil.find_npp_viirs_filesets(input_directory)
        if len(filesets) == 0:
            logger.warning(f'не найдено ни одного датасета в папке {input_directory}')
        logger.debug(f'найдено {len(filesets)} в папке {input_directory}')

        for fs in filesets:
            # обработка данных с level1
            typ = fs.geoloc_file.file_type.upper()
            l1_output_file = _mkpath(self._processed_output / fs.geoloc_file.date.strftime('%Y%m%d') / fs.swath_id) \
                             / f'{fs.root_dir.parts[-1]}.{typ}.tiff'
            if not l1_output_file.is_file():
                self._on_before_processing(str(l1_output_file), typ)
                try:
                    _process.process_fileset(fs, str(l1_output_file), self._get_scale(fs.geoloc_file.band))
                except Exception as exc:
                    self._on_exception(exc)
                    raise

                self._on_after_processing(str(l1_output_file), typ)

            processed: ProcessedViirsL1 = ProcessedViirsL1.get_or_none(ProcessedViirsL1.output_file == l1_output_file)
            if processed is None:
                # сохранить данные в БД
                processed = ProcessedViirsL1(l1_output_file, fs.geoloc_file.date,
                                             geoloc_filename=fs.geoloc_file.path_obj.parts[-1],
                                             type=fs.geoloc_file.file_type,
                                             input_directory=input_directory)
                processed.save(True)
            elif processed.type != typ:
                # тип файла в БД не соответствует тому, что есть на самом деле
                # будем считать, что тип в БД неверен
                logger.warning(f'обноружил, что тип файла {processed.output_file} (id={processed.id}) в БД '
                               f'({processed.type}) не соответствует реальному ({typ}) тип будет заменен')
                processed.update({
                    ProcessedViirsL1.type: typ
                })

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
        # обработка NDVI
        self._process_ndvi_files(processed)

    def _produce_daily_products(self):
        logger.info('обработка ежедневных продуктов...')
        try:
            self._produce_merged_ndvi_file_for_today()
            self._process_ndvi_dynamics_for_today
        except Exception as e:
            self._on_exception(e)

    def _produce_maps(self):
        #self._produce_ndvi_maps()
        self._produce_ndvi_dynamics_maps()

    def _produce_ndvi_dynamics_maps(self, day=None):
        ndvi_dynamics = self._process_ndvi_dynamics_for_today
        if ndvi_dynamics is None:
            logger.warning(f'не могу создать карты динамки посевов т. к. не удалось создать динамику на сегодня')
            return
        ndvi_dynamics_dir = self._ndvi_dynamics_output / _todaystr()
        _mkpath(ndvi_dynamics_dir)
        # создание карт динамики
        self._on_before_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')
        date_text = ndvi_dynamics.date_text
        self._produce_images(ndvi_dynamics.output_file, str(ndvi_dynamics_dir),
                             date_text=date_text, builder=NDVIDynamicsMapBuilder)

        self._on_after_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')

    # region ndvi / ndvi dynamics

    def _process_cloud_mask(self, processed: ProcessedViirsL1) -> Path:
        level2_folder = os.path.join(processed.input_directory, 'viirs/level2')
        l2_input_file = glob(os.path.join(level2_folder, '*CLOUDMASK.tif'))

        is_single_file_mode = self._config.get('SINGLE_CLOUD_MASK_FILE', False)

        if is_single_file_mode:
            clouds_file = _mkpath(Path(f'/tmp/viirs_processor_{os.getpid()}'))
            clouds_file /= 'cloud_mask.tiff'
        else:
            try:
                clouds_root = self._config.get_output('clouds')
            except KeyError:
                clouds_root = self._processed_output

            clouds_file = _mkpath(clouds_root) / processed.dataset_date.strftime(
                '%Y%m%d') / f'{processed.directory_name}.PROJECTED_CLOUDMASK.tiff'

        if is_single_file_mode or not clouds_file.is_file() or self._config.get('FORCE_CLOUD_MASK_PROCESSING', False):
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

    def _process_ndvi_files(self, based_on: ProcessedViirsL1) -> NDVITiff:
        if not based_on.is_of_type('GIMGO'):
            raise ProcessingException('невозможно обработать NDVI')

        ndvi_file = _mkpath(
            self._processed_output / based_on.dataset_date.strftime('%Y%m%d') / based_on.swath_id
        ) / f'{based_on.directory_name}.NDVI.tiff'

        ndvi_record: NDVITiff = NDVITiff.get_or_none(NDVITiff.based_on == based_on)

        if not ndvi_file.is_file():
            clouds_file = self._process_cloud_mask(based_on)

            if os.path.isfile(based_on.output_file):
                self._on_before_processing(ndvi_file, 'ndvi')
                _process.process_ndvi(based_on.output_file, ndvi_file, str(clouds_file))

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
        days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.combine(datetime.now().date(), datetime.max.time())
        past_day = now - timedelta(days=days - 1)
        past_day = datetime.combine(past_day.date(), datetime.min.time())

        merged_ndvi_filename = 'merged_ndvi_' + now.strftime('%Y%m%d') + '_' + past_day.strftime('%Y%m%d') + '.tiff'
        output_file = _mkpath(self._processed_output / _todaystr() / 'daily') / merged_ndvi_filename
        ndvi_records = NDVITiff.select() \
            .join(ProcessedViirsL1) \
            .where((ProcessedViirsL1.dataset_date <= now) & (ProcessedViirsL1.dataset_date >= past_day))
        ndvi_records: List[NDVITiff] = list(ndvi_records)

        if not output_file.is_file() or self._config.get('FORCE_NDVI_COMPOSITE_PROCESSING', True):
            # если не одного NDVI tiff'а не найдено, выбросить исключение
            if len(ndvi_records) == 0:
                no_ndvi_count = ProcessedViirsL1.select_gimgo_without_ndvi().count()
                if no_ndvi_count > 0:
                    logger.warning(f'найдено {no_ndvi_count} обработанных GIMGO снимков, '
                                   f'которые не имеют соответствующих NDVI')
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                raise ProcessingException(
                    'не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')

            for raster in ndvi_records:
                if not os.path.isfile(raster.output_file):
                    logger.error(f'файл {raster} не найден, обнаружено несоотсветсвие БД')
            ndvi_rasters = list(filter(lambda r: os.path.isfile(r.output_file), ndvi_records))
            ndvi_rasters = list(map(lambda r: r.output_file, ndvi_rasters))
            self._on_before_processing(str(output_file), 'merged_ndvi')
            merge_files2tiff(ndvi_rasters, str(output_file), method='max')
            self._on_after_processing(str(output_file), 'merged_ndvi')

        composite = NDVIComposite.get_or_none(NDVIComposite.output_file == str(output_file))

        if composite is None:
            composite = NDVIComposite(output_file, starts_at=past_day.date(), ends_at=now.date())
            composite.save(True)
            assoc = [
                NDVICompositeComponents(composite=composite, component=record)
                for record in ndvi_records
            ]
            NDVICompositeComponents.bulk_create(assoc)

        return composite

    # endregion

    # region maps

    def _produce_ndvi_maps(self):
        force_merged_ndvi = self._config.get('FORCE_MERGED_NDVI_PRODUCING', True)
        if force_merged_ndvi:
            merged_ndvi = self._produce_merged_ndvi_file_for_today()
        else:
            merged_ndvi = NDVIComposite.get_or_none(NDVIComposite.ends_at == datetime.now().date())
            if merged_ndvi is None:
                logger.warning('не удалось сгенерировать NDVI карты, так как композит NDVI не найден, а '
                               'FORCE_MERGED_NDVI_PRODUCING = False, поэтому нельзя сгенерировать NDVI карты')
                return
        png_dir = str(_mkpath(self._ndvi_output / _todaystr()))
        date_text = merged_ndvi.date_text
        self._produce_images(merged_ndvi.output_file, png_dir, date_text)

    @property
    def _process_ndvi_dynamics_for_today(self) -> Optional[NDVIDynamicsTiff]:
        now = datetime.now().date()
        days = self._config.get(
            'NDVI_DYNAMICS_PERIOD',
            self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5) * 2
        )
        past_days = now - timedelta(days=days - 1)
        b2: NDVIComposite = NDVIComposite.get_or_none(NDVIComposite.ends_at == now)
        b1: NDVIComposite = NDVIComposite.get_or_none(NDVIComposite.starts_at == past_days)

        if b1 is None:
            logger.warning(f'не удалось найти композит начинающийся с starts_at={past_days} (b1)')
            return None
        if b2 is None:
            logger.error(f'не удалось найти композит, сделанный сегодня (b2, ends_at={now})')
            return None

        if (b1.ends_at - b2.starts_at).days > 1:
            logger.warning(f'похоже, что композиты {b1} и {b2} имеют неправильные даты - между концом композита {b1} и'
                           f' датой начала {b2} более 1 дня ({b1.ends_at - b2.starts_at})')

        filename = '.'.join((
            f'ndvi_dynamics',
            f'{b1.starts_at.strftime("%Y%m%d")}-{b1.ends_at.strftime("%Y%m%d")}',
            f'{b2.starts_at.strftime("%Y%m%d")}-{b2.ends_at.strftime("%Y%m%d")}',
            'tiff'
        ))
        dynamics_tiff_output = _mkpath(self._processed_output / _todaystr() / 'daily') / filename

        if not dynamics_tiff_output.is_file() or self._config.get('FORCE_NDVI_DYNAMICS_PROCESSING', True):
            self._on_before_processing(str(dynamics_tiff_output), 'ndvi_dynamics')
            _process.process_ndvi_dynamics(b1.output_file, b2.output_file, str(dynamics_tiff_output))
            self._on_after_processing(str(dynamics_tiff_output), 'ndvi_dynamics')

        record: NDVIDynamicsTiff = NDVIDynamicsTiff.get_or_none(
            (NDVIDynamicsTiff.b1_composite == b1) & (NDVIDynamicsTiff.b2_composite == b2))
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
            logger.debug(f'обработка изображения ({index + 1}/{len(png_config)}) {filepath}')
            force_regeneration = self._config.get('FORCE_MAPS_REGENERATION', True)
            if os.path.isfile(filepath) and not force_regeneration:
                continue
            if force_regeneration and os.path.isfile(filepath):
                logger.debug(f'перезаписываю {filepath}')
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

            produce_image(input_file, filepath,
                          builder=builder,
                          logo_path=self._config['LOGO_PATH'],
                          iso_sign_path=self._config['ISO_QUALITY_SIGN'],
                          shp_mask_file=shapefile, **props)

    # endregion
