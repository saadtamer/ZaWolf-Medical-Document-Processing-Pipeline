from src.database.database import Database


class PhotoRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        treatment_id=None,
        photo_type=None,
        taken_at=None,
        file_ref=None,
    ):
        query = """
        INSERT INTO photos (
            client_id,
            treatment_id,
            type,
            taken_at,
            file_ref
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            treatment_id,
            photo_type,
            taken_at,
            file_ref,
        )

        return self.db.insert_and_get_id(query, params)