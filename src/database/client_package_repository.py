from src.database.database import Database


class ClientPackageRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        package_id,
        remaining_sessions=None,
        expires_at=None,
    ):
        query = """
        INSERT INTO client_packages (
            client_id,
            package_id,
            remaining_sessions,
            expires_at
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
        """

        params = (
            client_id,
            package_id,
            remaining_sessions,
            expires_at,
        )

        return self.db.insert_and_get_id(query, params)