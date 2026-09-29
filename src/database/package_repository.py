from src.database.database import Database


class PackageRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        name,
        sessions_count=None,
        price=None,
        validity_days=None,
    ):
        query = """
        INSERT INTO packages (
            name,
            sessions_count,
            price,
            validity_days
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
        """

        params = (
            name,
            sessions_count,
            price,
            validity_days,
        )

        return self.db.insert_and_get_id(query, params)