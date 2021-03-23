import importlib
import sys
from contextlib import contextmanager

import loguru
import peewee

from gdal_viirs import misc
from gdal_viirs.config import load_config, ConfigWrapper
from gdal_viirs.hl import NPPProcessor
from gdal_viirs.persistence.models import db_proxy, PEEWEE_MODELS


def _set_debug_off():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, colorize=True, level='INFO')


@contextmanager
def setup_env(config):
    config = load_config(config)

    try:
        # config directory
        config_dir = misc.to_path(config['CONFIG_DIR'])
        config_dir.mkdir(parents=True, exist_ok=True)

        # db
        db = peewee.SqliteDatabase(str(config_dir / 'viirs_processor.db'))
        db_proxy.initialize(db)
        db.create_tables(PEEWEE_MODELS)

        yield config
    finally:
        db_proxy.initialize(None)


def create_npp_processor(config: ConfigWrapper) -> NPPProcessor:
    """
    Создает процессор с указанной конфигурацией.
    :param config: модуль конфигурации (полученный через import), строка для импорта или словарь
    :return: NPPProcessor или экземпляр класса указанного как BUILDER_CLASS в конфиге
    """
    if not config.get('IS_DEBUG'):
        _set_debug_off()
    processor_class = config.get('BUILDER_CLASS', NPPProcessor)
    processor = processor_class(config)
    return processor


def process_recent(config):
    with setup_env(config) as config:
        create_npp_processor(config).process_recent()


def produce_products(config):
    with setup_env(config) as config:
        create_npp_processor(config).produce_products()


def produce_maps(config):
    with setup_env(config) as config:
        create_npp_processor(config).produce_maps()
