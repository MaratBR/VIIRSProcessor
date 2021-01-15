import importlib
import inspect
import os
import sys

import loguru

from gdal_viirs.hl import _default_config, NPPProcessor


def _set_debug_off():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, colorize=True, level='INFO')


def create_npp_processor(config=_default_config):
    if isinstance(config, str):
        if os.path.isfile(config):
            if config.endswith('.py'):
                config = config[:3]
        config = importlib.import_module(config).__dict__
    elif inspect.ismodule(config):
        config = config.__dict__
    config = dict(filter(lambda kv: not kv[0].startswith('__') and not inspect.ismodule(kv[1]), config.items()))

    if config.get('IS_DEBUG') == False:
        _set_debug_off()
    processor_class = config.get('BUILDER_CLASS', NPPProcessor)
    processor = processor_class(config)
    return processor


def process_recent(config=_default_config):
    create_npp_processor(config).process_recent()