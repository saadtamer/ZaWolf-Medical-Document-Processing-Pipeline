from src.database.database import Database


class ConsentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        appointment_id=None,
        consent_type=None,
        signed_at=None,
        file_ref=None,
    ):
        query = """
        INSERT INTO consents (
            client_id,
            appointment_id,
            consent_type,
            signed_at,
            file_ref
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            appointment_id,
            consent_type,
            signed_at,
            file_ref,
        )

        return self.db.insert_and_get_id(query, params)