import importlib
import inspect
import os
from contextlib import contextmanager
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent

CONFIG = {
    'SCALE_BAND_I': 375,
    'SCALE_BAND_M': 750,
    'SCALE_BAND_DN': 750,
    'CONFIG_DIR': str(_REPO_ROOT / 'viirs_processor_cfg')
}


def req_resource_path(res):
    return _REPO_ROOT / 'required_resources' / res


class ConfigWrapper(dict):
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], ConfigWrapper):
            return args[0]
        return dict.__new__(cls, *args, **kwargs)

    def __init__(self, *configs):
        super(ConfigWrapper, self).__init__()
        for cfg in configs:
            if inspect.ismodule(cfg):
                cfg = dict([
                    kv for kv in cfg.__dict__.items()
                    if not kv[0].startswith('__') and not inspect.ismodule(kv[1])
                ])
            elif not isinstance(cfg, (dict, ConfigWrapper)):
                raise TypeError('конфигурация не является модулем или словарем')
            self.update(cfg)

    def __getitem__(self, item):
        if '.' in item:
            return self.getpath(item)
        if item in self:
            return dict.__getitem__(self, item)

    def get(self, k, default=None):
        if isinstance(k, str) and '.' in k:
            try:
                return self.getpath(k)
            except KeyError:
                return default
        return dict.get(self, k, default)

    def getpath(self, item):
        parts = item.split('.')
        val = self
        for part in parts:
            try:
                val = dict.__getitem__(val, part)
            except TypeError:
                raise KeyError(item)
        return val

    def get_output(self, type_):
        return Path(os.path.expandvars(os.path.expanduser(self.getpath(f'OUTPUTS.{type_}'))))

    def get_input(self, type_):
        return Path(os.path.expandvars(os.path.expanduser(self.getpath(f'INPUTS.{type_}'))))


def load_config(config) -> ConfigWrapper:
    if isinstance(config, str):
        return ConfigWrapper(importlib.import_module(config))
    return ConfigWrapper(config)
