import sqlite3
from threading import Lock

class Database:
    def __init__(self, path):
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.lock = Lock()

    def __del__(self):
        if hasattr(self, "connection"):
            self.connection.close()

    def create_database(self, schema: dict):
        with self.lock:
            for table in schema["database"]["tables"]:
                table_name = list(table.keys())[0]
                table_def = table[table_name]
                fields = []
                for field in table_def["fields"]:
                    field_name = list(field.keys())[0]
                    field_def = field[field_name]
                    fields.append(f"{field_name} {field_def}")
                req = f"CREATE TABLE IF NOT EXISTS {table_name} (\n "
                req += ",\n ".join(fields)
                req += "\n);"
                print(f"Создаем таблицу с запросом: {req}")
                self.cursor.execute(req)
                req = ""
            self.connection.commit()
            print("База данных создана")

    def execute(self, query, params=()):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        
    def fetchone(self, query, params=()):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        
    def fetchall(self, query, params=()):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()