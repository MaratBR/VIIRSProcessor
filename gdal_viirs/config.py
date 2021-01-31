import inspect
import os
from pathlib import Path

CONFIG = {
    'SCALE': 1000,
    'CONFIG_DIR': os.path.expanduser('./viirs_processor_cfg')
}


def req_resource_path(res):
    return Path(__file__).parent.parent / 'required_resources' / res


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
