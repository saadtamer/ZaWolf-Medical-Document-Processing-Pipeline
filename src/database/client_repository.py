from src.database.database import Database


class ClientRepository:
    def __init__(self):
        self.db = Database()

    def create(self, client):
        query = """
        INSERT INTO clients (
            first_name,
            last_name,
            dob,
            gender,
            mobile,
            email,
            address,
            lead_source,
            medical_alerts,
            opt_in_sms
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client.get("first_name"),
            client.get("last_name"),
            client.get("dob"),
            client.get("gender"),
            client.get("mobile"),
            client.get("email"),
            client.get("address"),
            client.get("lead_source"),
            client.get("medical_alerts"),
            client.get("opt_in_sms"),
        )

        result = self.db.fetch_one(query, params)
        return result[0]