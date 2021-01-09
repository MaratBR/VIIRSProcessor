import os
from datetime import datetime
from glob import glob
from pathlib import Path

from loguru import logger

from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs import process as _process, utility as _utility


class NPPProcessor:
    def __init__(self, data_dir: str, output_dir: str, config_dir='~/.viirs_processor', scale=2000):
        config_dir = Path(os.path.expandvars(os.path.expanduser(config_dir)))
        config_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(config_dir / 'store.db'))
        self._output_dir = os.path.expandvars(os.path.expanduser(output_dir))
        self._data_dir = os.path.expandvars(os.path.expanduser(data_dir))
        Path(self._data_dir).mkdir(parents=True, exist_ok=True)
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)
        self.scale = scale

    def _dirname(self, d, kind, ext='tiff'):
        return os.path.join(self._output_dir, d + '.' + kind + '.' + ext)

    def process_recent(self):
        directories = glob(os.path.join(self._data_dir, '*'))
        for d in directories:
            if not os.path.isdir(d):
                continue
            self._process_directory(d)

    def reset(self):
        self.persistence.delete_meta('last_check_time')
        self.persistence.reset()

    def _process_directory(self, d):
        dirname = os.path.basename(d)
        if not self.persistence.has_processed(d, 'level1'):
            filesets = _utility.find_sdr_viirs_filesets(os.path.join(d, 'viirs/level1')).values()
            for fs in filesets:
                output_file = self._dirname(dirname, fs.geoloc_file.file_type)
                _process.process_fileset(fs, output_file, self.scale)
            self.persistence.add_processed(d, 'level1')

        clouds_file = self._dirname(dirname, 'PROJECTED_CLOUDMASK')

        if not self.persistence.has_processed(d, 'cloud_mask'):
            input_file = glob(os.path.join(d, 'viirs/level2/*CLOUDMASK.tif'))
            if len(input_file) != 0:
                input_file = input_file[0]
                _process.process_cloud_mask(input_file, clouds_file, scale=self.scale)
                self.persistence.add_processed(d, 'cloud_mask', clouds_file)


        if self.persistence.has_processed(d, 'cloud_mask') and not self.persistence.has_processed(d, 'ndvi', strict=True):
            ndvi_file = self._dirname(dirname, 'NDVI')
            gimgo_tiff_file = self._dirname(dirname, 'GIMGO')
            if os.path.isfile(gimgo_tiff_file):
                _process.process_ndvi(gimgo_tiff_file, ndvi_file, clouds_file)
                self.persistence.add_processed(d, 'ndvi', ndvi_file)

            else:
                logger.warning(f'не удалось найти файл {gimgo_tiff_file}, не могу обработать NDVI')

        png_filetype = datetime.now().strftime('PNG_%Y_%m_%d')



