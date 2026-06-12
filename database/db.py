import sqlite3
import threading

class Database:
    def __init__(self, path):
        self.path = path
        self._local = threading.local()
    
    def _get_connection(self):
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
            self._local.cursor = self._local.connection.cursor()
        return self._local.connection
    
    @property
    def connection(self):
        return self._get_connection()
    
    @property
    def cursor(self):
        return self._get_connection().cursor()
    
    def execute(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
        
    def fetchone(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
        
    def fetchall(self, query, params=()):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def close(self):
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
