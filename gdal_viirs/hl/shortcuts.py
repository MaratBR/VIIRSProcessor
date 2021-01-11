import importlib
import inspect
import os

from gdal_viirs.hl import _default_config, NPPProcessor


def create_npp_processor(config=_default_config):
    if isinstance(config, str):
        if os.path.isfile(config):
            if config.endswith('.py'):
                config = config[:3]
        config = importlib.import_module(config).__dict__
    elif inspect.ismodule(config):
        config = config.__dict__

    processor_class = config.get('BUILDER_CLASS', NPPProcessor)
    args = config.get('BUILDER_ARGS', {})
    args['data_dir'] = config['INPUT_DIR']
    args['output_dir'] = config['OUTPUT_DIR']
    args['png_config'] = config['PNG_CONFIG']
    args['map_points'] = config.get('MAP_POINTS')
    if 'CONFIG_DIR' in config:
        args['config_dir'] = config['CONFIG_DIR']
    if 'SCALE' in config:
        args['scale'] = config['SCALE']
    processor = processor_class(**args)
    return processor


def process_recent(config=_default_config):
    create_npp_processor(config).process_recent()