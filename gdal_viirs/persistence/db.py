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
            created_at_ts INTEGER,
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

    def has_processed(self, name: str, src_type: str, strict=False):
        result = next(self._db.execute(
            'SELECT EXISTS(SELECT 1 FROM processed_data_sources WHERE name = ? AND type = ?)', (name, src_type)))
        if result[0] != 1:
            return False
        if not strict:
            return True
        output = next(v[0] for v in self._db.execute(
            'SELECT output FROM processed_data_sources WHERE name = ? AND type = ?', (name, src_type)))
        if output is None or (output != '' and not os.path.isfile(output)):
            logger.error('не удалось найти файл, который помечен как обработанный strict=True, поэтому этот файл'
                         ' будет удален из БД, так как он не найден или информация о нём отсутсвует в БД')
            self.delete_processed(name, src_type)
            return False
        return True

    def add_processed(self, name: str, src_type: str = None, output: str = None, created_at: int = None):
        logger.debug(name)
        now = datetime.now().timestamp()
        query = 'INSERT INTO processed_data_sources(name, type, added_at_ts, output, created_at_ts) ' \
                'VALUES (?, ?, ?, ?, ?)'
        self._db.execute(query, (name, src_type, now, output, created_at or now))
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

    def query(self, query, params):
        yield from self._db.execute(query, params)

    def query_processed(self, where, params, select='*'):
        return self.query(f'SELECT {select} FROM processed_data_sources WHERE {where}', params)

    def reset(self):
        self._db.execute('DELETE FROM processed_data_sources')
        self._db.commit()