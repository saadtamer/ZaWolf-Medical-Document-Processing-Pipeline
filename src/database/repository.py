from src.database.database import Database


class Repository:
    def __init__(self, table_name):
        self.db = Database()
        self.table_name = table_name

    def insert(self, data, cursor=None):
        columns = list(data.keys())
        values = list(data.values())

        column_names = ", ".join(columns)
        placeholders = ", ".join("?" for _ in values)

        query = f"""
        INSERT INTO {self.table_name} ({column_names})
        OUTPUT INSERTED.id
        VALUES ({placeholders})
        """

        if cursor:
            cursor.execute(query, values)
            return cursor.fetchone()[0]

        return self.db.insert_and_get_id(query, values)

    def get_by_id(self, record_id):
        query = f"""
        SELECT *
        FROM {self.table_name}
        WHERE id = ?
        """

        return self.db.fetch_one(query, (record_id,))