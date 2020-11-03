import os
from datetime import datetime, time
from typing import NamedTuple, List, Optional, TypeVar, Union, Tuple

import gdal
import numpy as np
import pyproj

DatasetLike = Union[gdal.Dataset, str, 'GeofileInfo']
TNumpyOperable = TypeVar('TNumpyOperable', np.ndarray, float, int)
Number = Union[int, float]


class Point(NamedTuple):
    x: Number
    y: Number


class GeoPoint(NamedTuple):
    lat: Number
    lon: Number


class GeofileInfo:
    GEOLOC_SDR = ['GITCO', 'GMTCO', 'GIMGO', 'GMODO', 'GDNBO']
    GEOLOC_EDR = ['GIGTO', 'GMGTO', 'GNCCO']
    GEOLOC = GEOLOC_EDR + GEOLOC_SDR

    I_BAND_SDR__REFLECTANCE = ['SVI01', 'SVI02', 'SVI03']
    I_BAND_SDR__BRIGHT_TEMP = ['SVI04', 'SVI05']
    I_BAND_SDR = I_BAND_SDR__REFLECTANCE + I_BAND_SDR__BRIGHT_TEMP

    M_BAND_SDR__REFLECTANCE = ['SVM01', 'SVM02', 'SVM03', 'SVM04', 'SVM05', 'SVM06', 'SVM07', 'SVM08', 'SVM09', 'SVM10',
                               'SVM11']
    M_BAND_SDR__BRIGHT_TEMP = ['SVM12', 'SVM13', 'SVM14', 'SVM15', 'SVM16']
    M_BAND_SDR = M_BAND_SDR__REFLECTANCE + M_BAND_SDR__BRIGHT_TEMP

    I_BAND_EDR = ['VI1BO', 'VI2BO', 'VI3BO', 'VI4BO', 'VI5BO']
    M_BAND_EDR = ['VM01O', 'VM02O', 'VM03O', 'VM04O', 'VM05O', 'VM06O']

    DNB_SDR = 'SVDNB'
    NCC_EDR = 'VNCCO'

    KNOWN_TYPES = GEOLOC + I_BAND_SDR + M_BAND_SDR + I_BAND_EDR + M_BAND_EDR + [DNB_SDR, NCC_EDR]

    path: str
    name: str
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
        self.path = path
        self.name = os.path.basename(path)
        parts = self.name.split('_', 7)
        self.file_type = parts[0]
        self.sat_id = parts[1]
        self.date = datetime.strptime(parts[2][1:], '%Y%m%d')
        self.t_start = self._parse_time(parts[3][1:])
        self.t_end = self._parse_time(parts[4][1:])
        self.orbit_number = parts[5]
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
        if self.file_type in self.I_BAND_EDR or self.file_type in self.I_BAND_SDR:
            return 'I'
        if self.file_type in self.M_BAND_EDR or self.file_type in self.M_BAND_SDR:
            return 'M'
        return None

    @property
    def is_known_type(self):
        return self.file_type in self.KNOWN_TYPES

    @property
    def is_geoloc(self):
        return self.file_type in self.GEOLOC


class ProcessedBandFile(NamedTuple):
    data: np.ndarray
    resolution: int


class ProcessedBandsSet(NamedTuple):
    geotransform: List[Number]
    bands: List[Tuple[ProcessedBandFile, Point]]
    band: str


class ProcessedGeolocFile(NamedTuple):
    info: GeofileInfo
    lat: np.ndarray
    lon: np.ndarray
    x_index: np.ndarray
    y_index: np.ndarray
    lonlat_mask: np.ndarray
    geotransform_min_x: Number
    geotransform_max_y: Number
    projection: pyproj.Proj


class ViirsFileSet(NamedTuple):
    geoloc_file: GeofileInfo
    m_band: List[GeofileInfo]
    i_band: List[GeofileInfo]


class ProcessedFileSet(NamedTuple):
    geoloc_file: ProcessedGeolocFile
    i_band: Optional[ProcessedBandsSet]
    m_band: Optional[ProcessedBandsSet]

    @property
    def bands(self):
        return [
            self.i_band,
            self.m_band
        ]

