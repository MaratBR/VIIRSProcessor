import os
import warnings
import uuid
from glob import glob

from urllib.request import urlopen
from zipfile import ZipFile

from gdal_viirs._config import CONFIG


def get_russia_admin_shp(level):
    filepath = os.path.join(CONFIG['RESOURCES_DIR'], f'admin_level_{level}.shp')
    if os.path.isfile(filepath):
        return filepath
    warnings.warn(f'Файл {filepath} не найден, скачиваю c mydata.biz...')
    tmp_file = os.path.join('/tmp', 'viirs-' + uuid.uuid4().hex + '.zip')
    with urlopen(CONFIG['_RUSSIAN_ADMIN_ZIP_URL']) as conn:
        with open(tmp_file, 'wb') as f:
            f.write(conn.read())
        with ZipFile(tmp_file) as f:
            f.extractall(CONFIG['RESOURCES_DIR'])

    if os.path.isfile(filepath):
        return filepath
    raise FileNotFoundError(filepath)

