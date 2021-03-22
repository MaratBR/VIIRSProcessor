import json
import os
import signal
import sys
from datetime import datetime, timedelta, date
from glob import glob
from multiprocessing import Pool
from pathlib import Path
from typing import List, Optional

from loguru import logger

import gdal_viirs.hl.utility as _hlutil
from gdal_viirs import process as _process, misc
from gdal_viirs.config import CONFIG, ConfigWrapper
from gdal_viirs.exceptions import ProcessingException
from gdal_viirs.maps import produce_image
from gdal_viirs.maps.ndvi_dynamics import NDVIDynamicsMapBuilder
from gdal_viirs.merge import merge_files2tiff
from gdal_viirs.persistence.models import *


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

    if 'WIDTH' not in config or not isinstance(config['WIDTH'], int):
        raise TypeError('значение WIDTH должно быть указано в конфигурации и должно быть целым числом')

    if 'HEIGHT' not in config or not isinstance(config['HEIGHT'], int):
        raise TypeError('значение HEIGHT должно быть указано в конфигурации и должно быть целым числом')

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


class NPPProcessor:
    def __init__(self, config=None):
        config = ConfigWrapper(CONFIG, config)
        _validate_config(config)

        config_dir = Path(os.path.expandvars(os.path.expanduser(config['CONFIG_DIR'])))
        config_dir.mkdir(parents=True, exist_ok=True)

        self._viirs_data_input = config.get_input('data')

        # путь к папке с готовыми тифами, которые программа сгенерирует
        self._processed_output = _mkpath(config.get_output('processed_data'))
        # выходная папка для карт ndvi, будет создана, если её еще нет
        self._ndvi_output = _mkpath(config.get_output('ndvi'))
        # папка для карт динамики, будет создана, если её еще нет
        self._ndvi_dynamics_output = _mkpath(config.get_output('ndvi_dynamics'))
        self._config = config

        self._init_logger()

        if 'DATE' in self._config and self._config['DATE'] is not None:
            logger.info('DATE = {}', self._config['DATE'])

    def _init_logger(self):
        logger_dir = self._config.get('LOG_PATH', 'viirs_logs')
        logger_file = os.path.join(logger_dir, 'viirs.log')
        logger.add(logger_file, rotation="100 MB", compression='tar.gz')

    @property
    def png_config(self):
        return self._config['PNG_CONFIG']

    @property
    def now(self):
        if 'DATE' in self._config and self._config['DATE'] is not None:
            date_val = self._config['DATE']
            if isinstance(date_val, str):
                date_val = datetime.strptime(date_val, '%d-%m-%Y')
            elif not isinstance(date_val, date):
                logger.warning('значение DATE в конфигурации неверно, должен быть экземпляр datetime.date или строка вида ДД-ММ-ГГГГ')
                return datetime.now()
            return datetime.combine(date_val.date(), datetime.now().time())
        elif 'DATE_OFFSET' in self._config and isinstance(self._config['DATE_OFFSET'], int):
            return datetime.now() - timedelta(days=self._config['DATE_OFFSET'])
        return datetime.now()

    def _find_viirs_directories(self):
        """
        Находит все папки, в которых есть VIIRS датасеты
        """
        directories = glob(os.path.join(self._viirs_data_input, '*'))
        directories = list(filter(os.path.isdir, directories))
        logger.debug(f'Найдено {len(directories)} папок с данными')
        return directories

    def process_recent(self):
        """
        Обрабатывает датасеты и создает карты
        :return:
        """
        self._on_start()
        self._produce_products()
        self._produce_maps()

    @logger.catch
    def produce_maps(self):
        """
        Создает карты, не обрабатывая датасеты и TIFF файлы
        :return:
        """
        self._on_start()
        self._produce_maps()

    @logger.catch
    def produce_products(self):
        self._on_start()
        self._produce_products()

    def _produce_products(self):
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
        MetaData.set_meta('last_start_pyversion', sys.version)
        MetaData.set_meta('packages_versions', misc.gather_packages())
        MetaData.set_meta('proj_version', misc.get_proj_version())

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
                processed.type = typ
                processed.save()

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
            self._process_ndvi_dynamics_for_today()
        except Exception as e:
            self._on_exception(e)

    def _produce_maps(self):
        self._produce_ndvi_maps()
        self._produce_ndvi_dynamics_maps()

    # region ndvi / ndvi dynamics

    def _process_cloud_mask(self, processed: ProcessedViirsL1) -> Path:
        """
        Обрабатывает маску облачности для данного обработанного датасета.
        :param processed: запись обработанного датасета
        :return: путь к файл или None, если не удалось найти исходник для маски облачности
        """
        level2_folder = os.path.join(processed.input_directory, 'viirs/level2')
        l2_input_file = glob(os.path.join(level2_folder, '*CLOUDMASK.tif'))

        is_single_file_mode = self._config.get('SINGLE_CLOUD_MASK_FILE', False)

        # если SINGLE_CLOUD_MASK_FILE = True сохраняем маску облачности в /tmp
        # если False - сохраняем в папку с данными по умолчанию
        if is_single_file_mode:
            clouds_file = _mkpath(Path('/tmp/viirs_processor'))
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
        """
        Создать NDVI файлы для указанного датасета
        :param based_on: запись обработанного датасета для которого следует создать NDVI файлы
        :return: экземпляр NDVITiff, сохранённый в БД
        """
        if not based_on.is_of_type('GIMGO'):
            raise ProcessingException('невозможно обработать NDVI')

        ndvi_file = _mkpath(
            self._processed_output / based_on.dataset_date.strftime('%Y%m%d') / based_on.swath_id
        ) / f'{based_on.directory_name}.NDVI.tiff'

        ndvi_record: NDVITiff = NDVITiff.get_or_none(NDVITiff.based_on == based_on)

        # создаем NDVI файл, но только если его еще нет, не перезаписываем
        if not ndvi_file.is_file():
            clouds_file = self._process_cloud_mask(based_on)

            # проверяем, что исходный файл (VIMGO/GIMGO) существует, если нет - ошибка
            if os.path.isfile(based_on.output_file):
                self._on_before_processing(ndvi_file, 'ndvi')
                _process.process_ndvi(based_on.output_file, ndvi_file, str(clouds_file))

                # сохраняем запись с БД
                tiff_record = NDVITiff.get_or_none(NDVITiff.output_file == ndvi_file)
                if tiff_record is None:
                    tiff_record = NDVITiff(ndvi_file)
                    tiff_record.based_on = based_on
                    tiff_record.save(True)
                elif tiff_record.based_on != based_on:
                    tiff_record.based_on = based_on
                    tiff_record.save()
                self._on_after_processing(ndvi_file, 'ndvi')
                return ndvi_file
            else:
                logger.warning(f'не удалось найти файл {based_on.output_file}, не могу обработать NDVI')
                raise ProcessingException(f'Файл GIMGO {based_on.output_file} не найден')
        else:
            logger.debug('пропускаем ndvi @ ' + str(ndvi_file))

        # создаем запись в БД
        if ndvi_record is None:
            ndvi_record = NDVITiff(ndvi_file, based_on=based_on)
            ndvi_record.save(True)
        elif ndvi_record.output_file != ndvi_file:
            ndvi_record.output_file = ndvi_file
            ndvi_record.save()
        return ndvi_record

    def _produce_merged_ndvi_file_for_today(self) -> Optional[NDVIComposite]:
        """
        Обрабатывает композит для сегодняшнего дня

        :raises: ProcessingException - если не найден ни один NDVI tiff
        :return: NDVIComposite
        """
        days = self._config.get('NDVI_MERGE_PERIOD_IN_DAYS', 5)
        now = datetime.combine(self.now.date(), datetime.max.time())
        past_day = now - timedelta(days=days - 1)
        past_day = datetime.combine(past_day.date(), datetime.min.time())

        merged_ndvi_filename = 'merged_ndvi_' + now.strftime('%Y%m%d') + '_' + past_day.strftime('%Y%m%d') + '.tiff'
        output_file = _mkpath(self._processed_output / self.now.strftime('%Y%m%d') / 'daily') / merged_ndvi_filename
        ndvi_records = NDVITiff.select() \
            .join(ProcessedViirsL1) \
            .where((ProcessedViirsL1.dataset_date <= now) & (ProcessedViirsL1.dataset_date >= past_day))
        ndvi_records: List[NDVITiff] = list(ndvi_records)

        if not output_file.is_file() or self._config.get('FORCE_NDVI_COMPOSITE_PROCESSING', True):
            # если не одного NDVI tiff'а не найдено, выбросить исключение
            ndvi_rasters = list(filter(lambda r: os.path.isfile(r.output_file), ndvi_records))
            ndvi_rasters = list(map(lambda r: r.output_file, ndvi_rasters))

            if len(ndvi_rasters) == 0:
                no_ndvi_count = ProcessedViirsL1.select_gimgo_without_ndvi().count()
                if no_ndvi_count > 0:
                    logger.warning(f'найдено {no_ndvi_count} обработанных GIMGO снимков, '
                                   f'которые не имеют соответствующих NDVI')
                logger.warning('не удалось создать объединение NDVI файлов, т. к. не найдено ни одного файла')
                return None

            for raster in ndvi_records:
                if not os.path.isfile(raster.output_file):
                    logger.error(f'файл {raster} не найден, обнаружено несоотсветсвие БД')

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

    def _process_ndvi_dynamics_for_today(self) -> Optional[NDVIDynamicsTiff]:
        now = self.now.date()
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
        dynamics_tiff_output = _mkpath(self._processed_output / self.now.strftime('%Y%m%d') / 'daily') / filename

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
            record.output_file = dynamics_tiff_output

        return record

    # endregion

    # region maps

    def _produce_ndvi_maps(self):
        """"""
        merged_ndvi = list(NDVIComposite.select().where(NDVIComposite.ends_at == self.now.date()))

        try:
            merged_ndvi = next(m for m in merged_ndvi if os.path.isfile(m.output_file))
        except StopIteration:
            if len(merged_ndvi) == 1:
                logger.error(f'Нашел композит за период {merged_ndvi.date_text}, но файл не найден: {merged_ndvi.output_file}')
            else:
                logger.error(f'Нашел {len(merged_ndvi)} композитов, но все композиты не были найдены в '
                             f'файловой системе: ' + ', '.join(m.output_file for m in merged_ndvi))
                return

        if merged_ndvi is None:
            logger.debug('не удалось найти композит на сегодня в БД, композит будет сгенерирован')
            merged_ndvi = self._produce_merged_ndvi_file_for_today()

            if merged_ndvi is None:
                logger.warning('не удалось сгенерировать композит на сегодня, карты не будут созданы')
                return

        if not os.path.isfile(merged_ndvi.output_file):
            logger.error(f'Не соответствие БД, файл не найден: {merged_ndvi.output_file}')
            return

        png_dir = str(_mkpath(self._ndvi_output / self.now.strftime('%Y%m%d')))
        date_text = merged_ndvi.date_text
        self._produce_images(merged_ndvi.output_file, png_dir, date_text)

    def _produce_ndvi_dynamics_maps(self):
        ndvi_dynamics = self._process_ndvi_dynamics_for_today()
        if ndvi_dynamics is None:
            logger.warning(f'не могу создать карты динамки посевов т. к. не удалось создать динамику на сегодня')
            return
        ndvi_dynamics_dir = self._ndvi_dynamics_output / self.now.strftime('%Y%m%d')
        _mkpath(ndvi_dynamics_dir)
        # создание карт динамики
        self._on_before_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')
        date_text = ndvi_dynamics.date_text
        self._produce_images(ndvi_dynamics.output_file, str(ndvi_dynamics_dir),
                             date_text=date_text, builder=NDVIDynamicsMapBuilder)

        self._on_after_processing(str(ndvi_dynamics_dir), 'maps_ndvi_dynamics')


    @staticmethod
    def _mp_produce_images(v):
        index, total, path, args, kwargs = v
        try:
            logger.debug(f'обработка изображения ({index + 1}/{total}) {path}')
            produce_image(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    def _produce_images(self, input_file, output_directory, date_text=None, builder=None):
        png_config = self._config.get("PNG_CONFIG")
        arguments = []

        for index, png_entry in enumerate(png_config):
            name = png_entry['name']
            filename = f'{name}.png'
            filepath = os.path.join(output_directory, filename)
            force_regeneration = self._config.get('FORCE_MAPS_REGENERATION', True)
            if os.path.isfile(filepath) and not force_regeneration:
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
            props['layers'] = png_entry.get('layers')
            shapefile = png_entry.get('mask_shapefile')
            if shapefile is None:
                logger.warning(f'изображение с идентификатором {name} (png_config[{index}]) не имеет mask_shapefile')

            w, h = self._config['WIDTH'], self._config['HEIGHT']

            if 'invert_ratio' in props:
                rotate90 = props['invert_ratio']
                del props['invert_ratio']
                if rotate90:
                    w, h = h, w

            dpi = 100
            w, h = w / dpi, h / dpi

            value = index, len(png_config), filepath, (input_file, filepath), dict(
                builder=builder,
                expected_width=w,
                expected_height=h,
                dpi=dpi,
                logo_path=self._config['LOGO_PATH'],
                iso_sign_path=self._config['ISO_QUALITY_SIGN'],
                shp_mask_file=shapefile,
                **props
            )
            arguments.append(value)

        original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        processes = self._config.get('MULTIPROCESSING_PROCESSES', 2)
        if processes == 1:
            for v in arguments:
                index, total, path, args, kwargs = v
                logger.debug(f'обработка изображения ({index + 1}/{total}) {path}')
                produce_image(*args, **kwargs)
        else:
            pool = Pool(processes)
            signal.signal(signal.SIGINT, original_sigint_handler)

            logger.debug('начинаю обработку карт с {} дочерними процессами', processes)
            res = pool.map_async(self._mp_produce_images, arguments)

            try:
                res.get(3600000)
            except KeyboardInterrupt:
                print('\n* Ctrl-C: останавливаю пул процессов...')
                pool.terminate()
                exit(2)
            else:
                pool.close()
            pool.join()

    # endregion
