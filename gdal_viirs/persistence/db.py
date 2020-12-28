import json
import os
import sqlite3
from datetime import datetime

from loguru import logger

from gdal_viirs.types import ViirsFileset


class GDALViirsDB:
    INIT_EXEC = [
        '''            
        CREATE TABLE processed_data_sources(
            name VARCHAR(255) NOT NULL,
            type VARCHAR(255) NULL,
            added_at_ts INTEGER,
            output VARCHAR(1000) NULL,
            PRIMARY KEY (name, type)
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

    def has_processed(self, name: str, src_type: str):
        result = next(self._db.execute(
            'SELECT EXISTS(SELECT 1 FROM processed_data_sources WHERE name = ? AND type = ?)', (name, src_type)))
        return result[0] == 1

    def add_processed(self, name: str, src_type: str = None):
        logger.debug(name)
        now = datetime.now().timestamp()
        query = 'INSERT INTO processed_data_sources(name, type, added_at_ts) VALUES (?, ?, ?)'
        self._db.execute(query, (name, src_type, now))
        self._db.commit()

    def delete_processed(self, name: str, src_type: str):
        self._db.execute('DELETE FROM processed_data_sources WHERE name = ?', (name, src_type))
        self._db.commit()


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
        self._db.execute('DELETE FROM processed_data_sources')
        self._db.commit()