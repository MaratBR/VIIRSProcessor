import os
from datetime import datetime
from glob import glob
from pathlib import Path

from loguru import logger

from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs import process as _process, utility as _utility


class ViirsProcessor:
    def __init__(self, data_dir: str, output_dir: str, config_dir='~/.gdal_viirs', scale=2000):
        config_dir = Path(os.path.expandvars(os.path.expanduser(config_dir)))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(config_dir / 'store.db'))
        self._output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        self._data_dir = os.path.expandvars(os.path.expanduser(data_dir))
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        self.scale = scale

    def _dirname(self, d, kind):
        return os.path.join(self._output_dir, d + '.' + kind + '.tiff')

    def process_recent(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        for d in directories:
            if not os.path.isdir(d):
                continue
            dirname = os.path.basename(d)
            if not self.persistence.has_processed(d, 'level1'):
                filesets = _utility.find_sdr_viirs_filesets(os.path.join(d, 'viirs/level1')).values()
                for fs in filesets:
                    output_file = self._dirname(dirname, fs.geoloc_file.file_type)
                    _process.process_fileset(fs, output_file, self.scale)
                self.persistence.add_processed(d, 'level1')

            if not self.persistence.has_processed(d, 'level2'):
                input_file = glob(os.path.join(d, 'viirs/level2/*CLOUDMASK.tif'))
                if len(input_file) != 0:
                    input_file = input_file[0]
                    clouds_file = os.path.join(self._output_dir, dirname + '.PROJECTED_CLOUDMASK.tiff')
                    _process.process_cloud_mask(input_file, clouds_file, scale=self.scale)
                    ndvi_file = self._dirname(dirname, 'NDVI')
                    gimgo_tiff_file = self._dirname(dirname, 'GIMGO')
                    if os.path.isfile(gimgo_tiff_file):
                        _process.process_ndvi(gimgo_tiff_file, ndvi_file)
                    else:
                        logger.warning(f'не удалось найти файл {gimgo_tiff_file}, не могу обработать NDVI')

    def reset(self):
        self.persistence.delete_meta('last_check_time')
        self.persistence.reset()


