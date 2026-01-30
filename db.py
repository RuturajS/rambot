import sqlite3
import json
import os
from datetime import datetime

class DBHandler:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files(
                hash_id TEXT PRIMARY KEY,
                filename TEXT,
                upload_source TEXT,
                upload_date TIMESTAMP,
                file_path TEXT,
                metadata JSON
            )
        ''')
        conn.commit()
        conn.close()

    def add_file(self, hash_id, filename, upload_source, file_path, metadata=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO files (hash_id, filename, upload_source, upload_date, file_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (hash_id, filename, upload_source, datetime.now(), file_path, json.dumps(metadata or {})))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # File already exists (idempotency based on hash)
            return False
        finally:
            conn.close()

    def list_files(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM files ORDER BY upload_date DESC')
        rows = cursor.fetchall()
        conn.close()
        # Convert rows to dicts and handle timestamp formatting if needed, 
        # but returning raw strings for now is fine for MVP
        return [dict(row) for row in rows]

    def get_file(self, hash_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM files WHERE hash_id = ?', (hash_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
