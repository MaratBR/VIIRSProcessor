import importlib
import json
import os
from datetime import date, datetime
from pathlib import Path


def to_path(path) -> Path:
    if isinstance(path, Path):
        path = str(path)
    path = os.path.expandvars(os.path.expanduser(path))
    return Path(path)PACKAGES


def get_gdal_viirs_directory() -> Path:
    return Path(__file__).parent.parent


def gather_packages():
    try:
        versions = {}
        packages = 'pyproj', 'rasterio', 'peewee', 'matplotlib', 'numpy'
        for p in packages:
            try:
                ver = importlib.import_module(p).__version__ # noqa
                versions[p] = ver
            except Exception as exc:
                versions[p] = f'failed: {exc}'
        return json.dumps(versions)
    except Exception as exc:
        return f'failed: {exc}'


def get_proj_version():
    try:
        import subprocess
        proc = subprocess.Popen('proj', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stderr = proc.communicate()
        return stderr.decode('ascii').split('\n')[0]
    except Exception as exc:
        return f'exception: {exc}'


def julian2date(julian_date: str) -> date:
    return datetime.strptime(julian_date, '%j').date()
