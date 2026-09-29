from src.database.database import Database


class InvoiceRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        appointment_id=None,
        issue_date=None,
        subtotal=None,
        discount=None,
        tax=None,
        total=None,
        status=None,
    ):
        query = """
        INSERT INTO invoices (
            client_id,
            appointment_id,
            issue_date,
            subtotal,
            discount,
            tax,
            total,
            status
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            appointment_id,
            issue_date,
            subtotal,
            discount,
            tax,
            total,
            status,
        )

        return self.db.insert_and_get_id(query, params)