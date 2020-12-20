import json
import os
import sqlite3
from datetime import datetime

from loguru import logger

from gdal_viirs.persistence.exceptions import PersistenceError
from gdal_viirs.types import ViirsFileSet


class GDALViirsDB:
    INIT_EXEC = [
        '''            
        CREATE TABLE geoloc_files(
            name VARCHAR(255) UNIQUE PRIMARY KEY,
            full_path VARCHAR(1000) NOT NULL,
            added_at_ts INTEGER
        );
        ''',
        '''
        CREATE TABLE meta(
            key VARCHAR(255) PRIMARY KEY,
            value VARCHAR(1000)
        );
        '''
    ]

    def __init__(self, file: str):
        file_exists = os.path.isfile(file)
        self._db = sqlite3.connect(file)
        if not file_exists:
            for stmt in self.INIT_EXEC:
                self._db.execute(stmt)

    def has_file(self, name: str):
        result = next(self._db.execute('SELECT EXISTS(SELECT 1 FROM geoloc_files WHERE name = ?)', [name]))
        return result[0] == 1

    def has_fileset(self, fileset: ViirsFileSet):
        return self.has_file(fileset.geoloc_file.name)

    def add_fileset(self, fileset: ViirsFileSet, replace=False):
        if self.has_fileset(fileset):
            if replace:
                self.delete_fileset(fileset)
            else:
                return
        logger.debug(fileset.geoloc_file.name)
        now = datetime.now().timestamp()
        query = 'INSERT INTO geoloc_files(name, full_path, added_at_ts) VALUES (?, ?, ?)'
        self._db.execute(query, (fileset.geoloc_file.name, fileset.geoloc_file.path, now))
        self._db.commit()

    def delete_fileset(self, fileset: ViirsFileSet):
        self._db.execute('DELETE FROM files WHERE name = ?', [fileset.geoloc_file.name])
        self._db.commit()

    def _get_file_id(self, filename):
        try:
            return self._db.execute('SELECT id FROM files WHERE name = ?', [filename]).next()[0]
        except StopIteration:
            return None

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

    def reset_filesets(self):
        self._db.execute('DELETE FROM geoloc_files')
        self._db.commit()