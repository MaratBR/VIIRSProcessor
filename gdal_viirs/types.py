"""
types.py содержит объявление типов данных, которые используются в библиотеке.
Как классов так и просто type-hints
"""

import os
from datetime import datetime, time
from pathlib import Path
from typing import NamedTuple, List, TypeVar, Union, Tuple, Optional

import gdal
import pyproj
import numpy as np

from gdal_viirs.const import *
from gdal_viirs.exceptions import InvalidFileType, InvalidFilename

DatasetLike = Union[gdal.Dataset, str, 'GeofileInfo']
TNumpyOperable = TypeVar('TNumpyOperable', np.ndarray, float, int)
Number = Union[int, float]


class Point(NamedTuple):
    x: Number
    y: Number


class GeofileInfo:
    """
    Предоставляет информацию о VIIRS файле
    """

    GEOLOC_SDR = [GITCO, GMTCO, GIMGO, GMODO, GDNBO]
    GEOLOC_EDR = [GIGTO, GMGTO, GNCCO]

    GEOLOC_PARALLAX_CORRECTED = [GITCO, GMTCO]
    GEOLOC_SMOOTH_ELLIPSOID = [GIMGO, GMODO]

    _GEOLOC_SDR_I = GIMGO, GITCO
    _GEOLOC_SDR_M = GMODO, GMTCO

    I_BAND_SDR = ['SVI01', 'SVI02', 'SVI03', 'SVI04', 'SVI05']
    M_BAND_SDR = ['SVM01', 'SVM02', 'SVM03', 'SVM04', 'SVM05', 'SVM06', 'SVM07', 'SVM08', 'SVM09', 'SVM10', 'SVM11',
                  'SVM12', 'SVM13', 'SVM14', 'SVM15', 'SVM16']

    I_BAND_EDR = ['VI1BO', 'VI2BO', 'VI3BO', 'VI4BO', 'VI5BO']
    M_BAND_EDR = ['VM01O', 'VM02O', 'VM03O', 'VM04O', 'VM05O', 'VM06O']

    DNB_SDR = 'SVDNB'
    NCC_EDR = 'VNCCO'

    KNOWN_TYPES = GEOLOC_EDR + GEOLOC_SDR + I_BAND_SDR + M_BAND_SDR + I_BAND_EDR + M_BAND_EDR + [DNB_SDR, NCC_EDR]

    path_obj: Path
    name: str
    path: str
    sat_id: str
    file_type: str
    date: datetime
    t_start: time
    t_end: time
    orbit_number: str
    file_ts: str
    data_source: str


    @staticmethod
    def _parse_time(s: str):
        return time(hour=int(s[:2]), minute=int(s[2:4]), second=int(s[4:6]), microsecond=int(s[6]) * 100000)

    def __init__(self, path):
        """
        Инициализирует экземпляр
        :param path:
        """
        p = Path(os.path.expandvars(os.path.expanduser(path)))
        self.path = str(p)
        self.name = p.parts[-1]
        parts = self.name.split('_', 7)
        if len(parts) != 8:
            raise InvalidFilename(self.name)
        self.file_type = parts[0]
        self.sat_id = parts[1]
        self.date = datetime.strptime(parts[2][1:], '%Y%m%d')
        self.t_start = self._parse_time(parts[3][1:])
        self.t_end = self._parse_time(parts[4][1:])
        self.orbit_number = parts[5][1:]
        self.file_ts = parts[6]
        self.data_source = parts[7]

    def __repr__(self):
        if not self.is_known_type:
            info = 'UNKNOWN ' + self.file_type
        else:
            info = f'{self.record_type}, '
            band = self.band
            if band:
                info += 'band=' + band
            else:
                info += 'geoloc'
            info += ', type=' + self.file_type

        return f'<GeofileInfo {info}>'

    def get_band_dataset(self):
        """
        Возвращает название датасета (а если точнее последнюю часть название после "/"),
        в зависимости от канала и типа (SVIO1/SVM16 и прочее)
        :return: str|None
        """
        if self.is_geoloc:
            raise InvalidFileType('expected: band filetype, got: ' + self.file_type)
        if self.file_type in self.I_BAND_SDR:
            return 'Reflectance' if int(self.file_type[-1]) < 4 else 'BrightnessTemperature'
        elif self.file_type in self.M_BAND_SDR:
            return 'Reflectance' if int(self.file_type[-2:]) < 12 else 'BrightnessTemperature'
        elif self.file_type in (self.DNB_SDR, self.NCC_EDR):
            return 'Radiance'
        return None

    def get_band_files_types(self):
        """
        Возвращает список типов файлов каналов

        :raises InvalidFileType если метод вызван на экземпляре GeofileInfo, обозначающем файл канала (например SVI01)
        :returns список типов файлов (как строки)
        """
        if not self.is_geoloc:
            raise InvalidFileType('got: ' + self.file_type + ', required: geolocation filetype, one of ' + ', '.join(
                self.GEOLOC_SDR + self.GEOLOC_EDR))
        if self.file_type in (GIMGO, GITCO):
            return self.I_BAND_SDR
        elif self.file_type in (GMODO, GMTCO):
            return self.M_BAND_SDR
        elif self.file_type == GDNBO:
            return [self.DNB_SDR]
        elif self.file_type == GIGTO:
            return self.I_BAND_EDR
        elif self.file_type == GMGTO:
            return self.M_BAND_EDR
        elif self.file_type == GNCCO:
            return [self.NCC_EDR]
        else:
            raise ValueError('invalid file time')

    @property
    def is_sdr(self):
        return self.record_type == 'SDR'

    @property
    def is_edr(self):
        return self.record_type == 'EDR'

    @property
    def is_band(self):
        return self.band is not None

    @property
    def record_type(self):
        if self.file_type in self.GEOLOC_SDR or \
                self.file_type in self.I_BAND_SDR or \
                self.file_type in self.M_BAND_SDR or \
                self.file_type == self.DNB_SDR:
            return 'SDR'
        if self.file_type in self.GEOLOC_EDR or \
                self.file_type in self.I_BAND_EDR or \
                self.file_type in self.M_BAND_EDR or \
                self.file_type == self.NCC_EDR:
            return 'EDR'
        return None

    @property
    def band(self):
        if self.file_type in self.I_BAND_EDR or self.file_type in self.I_BAND_SDR or self.file_type in self._GEOLOC_SDR_I:
            return 'I'
        if self.file_type in self.M_BAND_EDR or self.file_type in self.M_BAND_SDR or self.file_type in self._GEOLOC_SDR_M:
            return 'M'
        if self.file_type in (self.NCC_EDR, self.DNB_SDR, GDNBO, GNCCO):
            return 'DN'
        return None

    @property
    def band_verbose(self):
        b = self.band
        if b == 'M':
            return 'M-band'
        elif b == 'I':
            return 'I-band'
        elif b == 'DN':
            return 'Day/Night'
        return b

    @property
    def is_known_type(self):
        return self.file_type in self.KNOWN_TYPES

    @property
    def is_geoloc(self):
        return self.file_type in self.GEOLOC_EDR or self.file_type in self.GEOLOC_SDR


class ProcessedGeolocFile(NamedTuple):
    info: GeofileInfo
    lonlat_mask: np.ndarray
    geotransform_min_x: Number
    geotransform_max_y: Number
    projection: pyproj.Proj
    scale: Number
    indexes_count: int
    out_image_shape: Tuple[int, int]

    indexes_ds: gdal.Dataset

    @property
    def x_index(self):
        return self.indexes_ds.GetRasterBand(1).ReadAsArray()[0]

    @property
    def y_index(self):
        return self.indexes_ds.GetRasterBand(1).ReadAsArray()[1]


class ProcessedBandFile(NamedTuple):
    data_ds: gdal.Dataset
    data_ds_band_index: int
    geoloc_file: ProcessedGeolocFile

    @property
    def data(self):
        return self.data_ds.GetRasterBand(self.data_ds_band_index).ReadAsArray()


class ProcessedBandsSet(NamedTuple):
    geotransform: List[Number]
    bands: List[Optional[ProcessedBandFile]]
    band: str


class ViirsFileSet(NamedTuple):
    geoloc_file: GeofileInfo
    band_files: List[GeofileInfo]

    def mtime(self):
        all_files = [self.geoloc_file] + self.band_files
        timestamps = map(lambda f: os.path.getmtime(f.path), all_files)
        return min(*timestamps)

    def is_full(self):
        b = self.geoloc_file.band
        if b == 'M':
            return len(self.band_files) == 16
        elif b == 'I':
            return len(self.band_files) == 5
        elif b == 'DN':
            return len(self.band_files) == 1
        else:
            raise InvalidFileType('could not detect band name, geoloc file type: ' + self.geoloc_file.file_type)


class ProcessedFileSet(NamedTuple):
    geoloc_file: ProcessedGeolocFile
    bands_set: ProcessedBandsSet
