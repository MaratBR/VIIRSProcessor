import os
import sqlite3
from datetime import datetime

from gdal_viirs.v2.types import ViirsFileSet

class GDALViirsDB:
    INIT_EXEC = [
        '''            
        CREATE TABLE files(
            name VARCHAR(255) UNIQUE PRIMARY KEY,
            full_path VARCHAR(1000) NOT NULL,
            added_at_ts INTEGER,
            geoloc_file VARCHAR(255) NULL,
            FOREIGN KEY(geoloc_file) REFERENCES files(name)
        );
        ''',
        '''
        CREATE TABLE processed_data(
            src_name VARCHAR(255),
            out_path VARCHAR(1000),
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
            return
        now = datetime.now().timestamp()
        records = []
        query = '''
            INSERT INTO files(name, full_path, added_at_ts, geoloc_file) VALUES (?, ?, ?, ?)
        '''
        for band_file in fileset.band_files:
            records.append((band_file.name, band_file.path, now, fileset.geoloc_file.name))
    
        self._db.execute(query, (fileset.geoloc_file.name, fileset.geoloc_file.path, now, None))
        self._db.executemany(query, records)
        self._db.commit()


