import pyodbc


class Database:
    def __init__(self):
        self.connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=ZaWolfDB;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

    def connect(self):
        return pyodbc.connect(self.connection_string)

    def execute(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def insert_and_get_id(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            connection.commit()
            return result[0]
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fetch_one(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            connection.close()

    def test_connection(self):
        result = self.fetch_one("SELECT DB_NAME()")
        return result[0]