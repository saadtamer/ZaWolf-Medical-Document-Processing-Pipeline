from src.database.database import Database


class RelationResolver:
    def __init__(self):
        self.db = Database()

    def _fetch_one(self, query, params, cursor=None):
        if cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
        else:
            result = self.db.fetch_one(query, params)

        return result[0] if result else None

    def find_client(self, client, cursor=None):
        query = """
        SELECT TOP 1 id
        FROM clients
        WHERE first_name = ?
          AND last_name = ?
          AND (
              mobile = ?
              OR (? IS NULL AND mobile IS NULL)
          )
        """

        params = (
            client.get("first_name"),
            client.get("last_name"),
            client.get("mobile"),
            client.get("mobile"),
        )

        return self._fetch_one(query, params, cursor)

    def find_staff(self, full_name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM staff WHERE full_name = ?",
            (full_name,),
            cursor,
        )

    def find_location(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM locations WHERE name = ?",
            (name,),
            cursor,
        )

    def find_service(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM services WHERE name = ?",
            (name,),
            cursor,
        )

    def find_product(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM products WHERE name = ?",
            (name,),
            cursor,
        )

    def find_package(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM packages WHERE name = ?",
            (name,),
            cursor,
        )