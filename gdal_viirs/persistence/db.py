import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Tuple, Optional

from loguru import logger

from gdal_viirs.types import ViirsFileset


def _tbl_name(name):
    return 'products_' + name


def _tbl_create(name, columns=None):
    columns = columns or ()
    if len(columns) == 0:
        return f'''
            CREATE TABLE {_tbl_name(name)}(
                output_path VARCHAR(255) PRIMARY KEY,
                created_at INTEGER
            );
            '''
    columns = ", \n".join(columns)
    return f'''
    CREATE TABLE {_tbl_name(name)}(
        output_path VARCHAR(255) PRIMARY KEY,
        created_at INTEGER,
        {columns}
    );
    '''


@dataclass
class NDVIComposite:
    path: Path
    from_date: datetime
    to_date: datetime


class GDALViirsDB:
    INIT_EXEC = [
        '''
        CREATE TABLE meta(
            key VARCHAR(255) PRIMARY KEY,
            value VARCHAR(60000)
        );
        ''',
        _tbl_create('ndvi', [
            'dataset_timestamp INTEGER'
        ]),
        _tbl_create('ndvi_dynamics', [
            'ds1_from INTEGER',
            'ds2_from INTEGER',
            'ds1_to INTEGER',
            'ds2_to INTEGER'
        ]),
        _tbl_create('ndvi_composite', [
            'from_date CHAR(8)',
            'to_date CHAR(8)'
        ])
    ]

    def __init__(self, file: str):
        file_exists = os.path.isfile(file)
        self._db = sqlite3.connect(file)
        if not file_exists:
            self._init_db()

    def _init_db(self):
        for stmt in self.INIT_EXEC:
            self._db.execute(stmt)
        self._db.commit()
        self.set_meta('ver', '1')

    def remove_processed(self, name, path):
        self._db.execute(f'DELETE FROM {_tbl_name(name)} WHERE output_path = ?', [path])
        try:
            self._db.commit()
        finally:
            self._db.rollback()

    def add_processed(self, name, path, **kwargs):
        path = str(path)
        now = int(datetime.now().timestamp())
        if len(kwargs) == 0:
            self._db.execute(
                f'INSERT INTO {_tbl_name(name)} (output_path, created_at) VALUES (?, ?)', [path, now])
        else:

            items = list(kwargs.items())
            keys = ', '.join(k for k, _ in items)
            placeholders = ', '.join('?' for _ in range(len(items)))
            values = [path, now] + [v for _, v in items]
            self._db.execute(
                f'INSERT INTO {_tbl_name(name)} (output_path, created_at, {keys}) VALUES (?, ?, {placeholders})',
                values)
        self._db.commit()

    def has_processed(self, name: str, path: str, strict=False):
        result = next(self._db.execute(
            f'SELECT EXISTS(SELECT 1 FROM {_tbl_name(name)} WHERE output_path = ?)', (str(path),)))
        if result[0] != 1:
            return False
        if not strict:
            return True
        if not os.path.exists(str(path)):
            logger.error('не удалось найти файл, который помечен как обработанный strict=True, поэтому этот файл'
                         ' будет удален из БД, так как он не найден или информация о нём отсутсвует в БД')
            self.delete_processed(name, path)
            return False
        return True

    def delete_processed(self, name: str, path: str):
        self._db.execute(f'DELETE FROM {_tbl_name(name)} WHERE output_path = ?', (str(path),))
        self._db.commit()

    def add_ndvi_composite(self, path: str, from_date: date, to_date: date):
        self.add_processed('ndvi_composite', path,
                           from_date=from_date.strftime('%Y%m%d'),
                           to_date=to_date.strftime('%Y%m%d'))

    def add_ndvi(self, path: str, dt: datetime):
        self.add_processed('ndvi', path,
                           dataset_timestamp=int(dt.timestamp()))

    def add_ndvi_dynamics(self, path: str,
                          ds1_timespan: Tuple[datetime, datetime],
                          ds2_timespan: Tuple[datetime, datetime]):
        assert ds1_timespan[0] < ds1_timespan[1]
        assert ds2_timespan[0] < ds2_timespan[1]
        self.add_processed('ndvi_dynamics', path,
                           ds1_from=int(ds1_timespan[0].timestamp()),
                           ds2_from=int(ds2_timespan[0].timestamp()),
                           ds1_to=int(ds1_timespan[1].timestamp()),
                           ds2_to=int(ds2_timespan[1].timestamp()))

    def _find(self, name, where=None, select='*', params=None):
        if where is None:
            return list(self._db.execute(f'SELECT {select} FROM {_tbl_name(name)}'))

        return list(self._db.execute(f'SELECT {select} FROM {_tbl_name(name)} WHERE {where}', params or ()))

    def find_ndvi(self, from_dt: datetime, to_dt: datetime = None):
        where = 'dataset_timestamp >= ?'
        params = [int(from_dt.timestamp())]

        if to_dt is not None:
            where += ' AND dataset_timestamp <= ?'
            params.append(int(to_dt.timestamp()))
        return [i[0] for i in self._find('ndvi', where, 'output_path', params)]

    def find_composite(self, starts_at: date = None, ends_at: date = None) -> Optional[NDVIComposite]:
        where = []
        params = []
        if starts_at is not None:
            where.append('from_date = ?')
            params.append(starts_at.strftime('%Y%m%d'))
        if ends_at is not None:
            where.append('to_date = ?')
            params.append(ends_at.strftime('%Y%m%d'))
        results = self._find('ndvi_composite',
                             where=' AND '.join(where),
                             select='output_path, from_date, to_date',
                             params=params)
        if len(results) == 0:
            return None
        return NDVIComposite(
            to_date=datetime.strptime(results[0][2], '%Y%m%d'),
            from_date=datetime.strptime(results[0][1], '%Y%m%d'),
            path=Path(results[0][0])
        )

    def get_meta(self, key, default_value=None):
        cur = self._db.execute('SELECT value FROM meta WHERE key = ?', [key])
        try:
            return json.loads(next(cur)[0])
        except StopIteration:
            return default_value

    def delete_meta(self, key: str):
        self._db.execute('DELETE FROM meta WHERE key = ?', [key])
        self._db.commit()
        logger.debug(key)

    def set_meta(self, key, value):
        self._db.execute('''
            INSERT INTO meta (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value;
            ''', [key, value])
        self._db.commit()
        logger.debug(f'{key} = {value}')

    def reset(self):
        self._db.execute('DELETE FROM processed')
        self._db.commit()