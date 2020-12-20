import os
from datetime import datetime
from functools import partial
from multiprocessing import Pool, Pipe
from pathlib import Path
from typing import List, Callable, Union

from loguru import logger

from gdal_viirs import utility, process
from gdal_viirs.persistence.db import GDALViirsDB
from gdal_viirs.save import save_fileset
from gdal_viirs.types import ViirsFileSet


class ViirsProcessor:
    def __init__(self, search_dirs: Union[Callable[[], List[str]], str, List[str]], out_dir: str, data_dir='~/.gdal_viirs',
                 make_ndvi = True, scale: int = 1000, use_multiprocessing=False, mp_processes=4):
        self.make_ndvi = make_ndvi
        self._mp_pool = Pool(mp_processes) if use_multiprocessing else None
        self.out_dir = os.path.expandvars(os.path.expanduser(out_dir))
        self.scale = scale
        self.search_dirs = [search_dirs] if isinstance(search_dirs, str) else search_dirs
        data_dir = Path(os.path.expandvars(os.path.expanduser(data_dir)))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.persistence = GDALViirsDB(str(data_dir / 'store.db'))

    def get_all_filesets(self):
        return self._find_filesets(return_all=True)

    def find_filesets(self):
        return self._find_filesets(return_all=False)

    def _find_filesets(self, *, return_all: bool):
        directories = self.search_dirs if isinstance(self.search_dirs, list) else self.search_dirs()
        directories = list(map(lambda d: os.path.expandvars(os.path.expanduser(d)), directories))
        if not return_all:
            last_check_ts = self.persistence.get_meta('last_check_time', 0)
            directories = list(filter(lambda directory: os.path.getmtime(directory) >= last_check_ts, directories))
        filesets = [
            utility.find_sdr_viirs_filesets(os.path.expandvars(os.path.expanduser(directory)))
            for directory in directories
        ]
        filesets = [item for d in filesets for item in d.values()]
        return filesets

    def _set_last_check_time(self):
        self.persistence.set_meta('last_check_time', datetime.now().timestamp())

    def process_recent_files(self):
        filesets = self.find_filesets()
        if len(filesets) > 0:
            logger.info(f'Нашел {len(filesets)} наборов файлов, начинаю обработку...')
        else:
            logger.debug('Наборы файлов не найдены')

        if self._mp_pool:
            print(filesets)
            self._mp_process_files(filesets)
        else:
            self._sp_process_files(filesets)

    def _sp_process_files(self, filesets):
        for fileset in filesets:
            if self.persistence.has_fileset(fileset):
                logger.debug(f'Набор файлов {fileset.geoloc_file.name} уже присутствует в БД и не будет обрабатываться')
            try:
                self._process_fileset(fileset)
            except Exception as e:
                logger.exception(e)
                return
        self._set_last_check_time()

    def _mp_process_files(self, filesets):
        parent, child = Pipe()
        to_be_processed = []
        for fs in filesets:
            if self.persistence.has_fileset(fs):
                logger.debug(f'Набор файлов {fs.geoloc_file.name} уже присутствует в БД и не будет обрабатываться')
            else:
                to_be_processed.append(fs)

        fn = partial(self.mp_process_fileset, child, self.out_dir, self.make_ndvi, self.scale)
        result = self._mp_pool.map_async(fn, to_be_processed)
        result.get()

    @staticmethod
    def mp_process_fileset(child, out_dir, make_ndvi, scale, fileset: ViirsFileSet):
        processed = process.hlf_process_fileset(fileset, scale=scale)
        save_fileset(out_dir, processed, make_ndvi)

    def _process_fileset(self, fileset: ViirsFileSet):
        processed = process.hlf_process_fileset(fileset, scale=self.scale)
        save_fileset(self.out_dir, processed, self.make_ndvi)
        self.persistence.add_fileset(fileset)

    def reset(self):
        self.persistence.delete_meta('last_check_time')
        self.persistence.reset_filesets()


