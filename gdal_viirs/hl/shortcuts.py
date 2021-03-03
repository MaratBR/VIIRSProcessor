import importlib
import sys

import loguru

from gdal_viirs.config import ConfigWrapper
from gdal_viirs.hl import NPPProcessor


def _set_debug_off():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, colorize=True, level='INFO')


def create_npp_processor(config) -> NPPProcessor:
    """
    Создает процессор с указанной конфигурацией.
    :param config: модуль конфигурации (полученный через import), строка для импорта или словарь
    :return: NPPProcessor или экземпляр класса указанного как BUILDER_CLASS в конфиге
    """
    if isinstance(config, str):
        config = importlib.import_module(config)
    config = ConfigWrapper(config)

    if not config.get('IS_DEBUG'):
        _set_debug_off()
    processor_class = config.get('BUILDER_CLASS', NPPProcessor)
    processor = processor_class(config)
    return processor


def process_recent(config):
    create_npp_processor(config).process_recent()


def produce_products(config):
    create_npp_processor(config).produce_products()


def produce_maps(config):
    create_npp_processor(config).produce_maps()
