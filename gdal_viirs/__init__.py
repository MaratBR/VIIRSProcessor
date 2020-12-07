import sqlite3

class PersistenceBackend:
    def __init__(self, db_file: str):
        self.db = sqlite3.connect(db_file)
