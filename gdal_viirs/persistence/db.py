import os
import sqlite3
from datetime import datetime

from gdal_viirs.types import ViirsFileSet


class GDALViirsDB:
    INIT_EXEC = [
        '''            
        CREATE TABLE files(
            id INTEGER PRIMARY KEY,
            name VARCHAR(255) UNIQUE PRIMARY KEY,
            full_path VARCHAR(1000) NOT NULL,
            added_at_ts INTEGER,
            geoloc_file_id INTEGER NULL,
            band CHAR(1) NULL,
            
            FOREIGN KEY(geoloc_file) REFERENCES files(id)
        );
        ''',
        '''
        CREATE TABLE processed_data(
            id INTEGER PRIMARY KEY,
            src_id INTEGER PRIMARY KEY,
            out_path VARCHAR(1000),
            type VARCHAR(255),
            created_at_ts INTEGER
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
        result = next(self._db.execute('SELECT EXISTS(SELECT 1 FROM files WHERE name = ?)', [name]))
        return result[0] == 1

    def has_fileset(self, fileset: ViirsFileSet):
        return self.has_file(fileset.geoloc_file.name)

    def add_fileset(self, fileset: ViirsFileSet, replace=False):
        if self.has_fileset(fileset):
            if replace:
                self.delete_fileset(fileset)
            else:
                return
        now = datetime.now().timestamp()
        query = '''
            INSERT INTO files(name, band, full_path, added_at_ts, geoloc_file_id) VALUES (?, ?, ?, ?, ?)
        '''
        cursor = self._db.cursor()

        cursor.execute(query, (fileset.geoloc_file.name, fileset.geoloc_file.band, fileset.geoloc_file.path, now, None))
        geoloc_id = cursor.lastrowid

        records = []
        for band_file in fileset.band_files:
            records.append((band_file.name, band_file.band, band_file.path, now, geoloc_id))

        cursor.executemany(query, records)

    def delete_fileset(self, fileset: ViirsFileSet):
        result = self._db.execute('''SELECT id FROM files WHERE name = ?''', [fileset.geoloc_file.name])
        try:
            (row_id,) = result.next()
        except StopIteration:
            return False

        self._db.execute('DELETE FROM files WHERE id = ? OR geoloc_file_id = ?', [row_id, row_id])
        return True
