from src.database.database import Database


class AppointmentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        staff_id,
        location_id,
        service_id,
        room=None,
        start_at=None,
        end_at=None,
        status=None,
        notes=None,
    ):
        query = """
        INSERT INTO appointments (
            client_id,
            staff_id,
            location_id,
            service_id,
            room,
            start_at,
            end_at,
            status,
            notes
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            staff_id,
            location_id,
            service_id,
            room,
            start_at,
            end_at,
            status,
            notes,
        )

        return self.db.insert_and_get_id(query, params)