import importlib
import inspect
import os

from gdal_viirs._config import CONFIG
from gdal_viirs.hl import _default_config, NPPProcessor


def create_npp_processor(config=_default_config):
    if isinstance(config, str):
        if os.path.isfile(config):
            if config.endswith('.py'):
                config = config[:3]
        config = importlib.import_module(config).__dict__
    elif inspect.ismodule(config):
        config = config.__dict__
    config = dict(filter(lambda kv: not kv[0].startswith('__'), config.items()))
    processor_class = config.get('BUILDER_CLASS', NPPProcessor)
    processor = processor_class(config)
    return processor


def process_recent(config=_default_config):
    create_npp_processor(config).process_recent()