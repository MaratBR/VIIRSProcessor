import importlib
import inspect
import os
import sys

import loguru

from gdal_viirs.config import ConfigWrapper
from gdal_viirs.hl import NPPProcessor


def _set_debug_off():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, colorize=True, level='INFO')


def create_npp_processor(config):
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
