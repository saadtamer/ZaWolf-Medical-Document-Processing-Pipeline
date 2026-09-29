from src.database.database import Database


class PaymentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        invoice_id,
        amount,
        method=None,
        paid_at=None,
        reference=None,
    ):
        query = """
        INSERT INTO payments (
            invoice_id,
            amount,
            method,
            paid_at,
            reference
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            invoice_id,
            amount,
            method,
            paid_at,
            reference,
        )

        return self.db.insert_and_get_id(query, params)