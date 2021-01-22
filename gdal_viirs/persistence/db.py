import json
import os
import sqlite3
from datetime import datetime

from loguru import logger

from gdal_viirs.types import ViirsFileset


class GDALViirsDB:
    INIT_EXEC = [
        '''            
        CREATE TABLE processed(
            path VARCHAR(255) NOT NULL PRIMARY KEY,
            type VARCHAR(255) NULL,
            added_at_ts INTEGER,
            created_at_ts INTEGER
        );
        ''',
        '''
        CREATE TABLE meta(
            key VARCHAR(255) PRIMARY KEY,
            value VARCHAR(1000)
        );
        ''',
        '''
        CREATE INDEX idx_processed_type
        ON processed (type);
        '''
    ]

    def __init__(self, file: str):
        file_exists = os.path.isfile(file)
        self._db = sqlite3.connect(file)
        if not file_exists:
            for stmt in self.INIT_EXEC:
                self._db.execute(stmt)

    def has_processed(self, path: str, strict=False):
        result = next(self._db.execute(
            'SELECT EXISTS(SELECT 1 FROM processed WHERE path = ?)', (str(path),)))
        if result[0] != 1:
            return False
        if not strict:
            return True
        if not os.path.exists(str(path)):
            logger.error('не удалось найти файл, который помечен как обработанный strict=True, поэтому этот файл'
                         ' будет удален из БД, так как он не найден или информация о нём отсутсвует в БД')
            self.delete_processed(path)
            return False
        return True

    def add_processed(self, path: str, src_type: str = None, created_at=None):
        logger.debug(path)
        now = datetime.now().timestamp()
        query = 'INSERT INTO processed(path, type, added_at_ts, created_at_ts) ' \
                'VALUES (?, ?, ?, ?)'
        self._db.execute(query, (str(path), src_type, now, created_at or now))
        self._db.commit()

    def delete_processed(self, name: str):
        self._db.execute('DELETE FROM processed WHERE path = ?', (str(name),))
        self._db.commit()

    def query(self, query, params):
        yield from self._db.execute(query, params)

    def query_processed(self, where, params, select='*'):
        return list(self.query(f'SELECT {select} FROM processed WHERE {where}', params))

    def find_processed(self, where, params):
        data = self.query_processed(where, params, 'path')
        result = []
        for (output,) in data:
            if os.path.isfile(output):
                result.append(output)
        return result

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