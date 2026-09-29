from src.database.database import Database


class TreatmentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        appointment_id,
        product_id,
        units=None,
        lot_number=None,
        expiry_date=None,
        area=None,
        injection_sites=None,
        depth=None,
        device_settings=None,
        skin_response=None,
        aftercare=None,
    ):
        query = """
        INSERT INTO treatment_records (
            appointment_id,
            product_id,
            units,
            lot_number,
            expiry_date,
            area,
            injection_sites,
            depth,
            device_settings,
            skin_response,
            aftercare
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            appointment_id,
            product_id,
            units,
            lot_number,
            expiry_date,
            area,
            injection_sites,
            depth,
            device_settings,
            skin_response,
            aftercare,
        )

        return self.db.insert_and_get_id(query, params)