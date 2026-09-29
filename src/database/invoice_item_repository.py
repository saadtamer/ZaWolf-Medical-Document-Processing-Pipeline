from src.database.database import Database


class InvoiceItemRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        invoice_id,
        item_type=None,
        item_id=None,
        description=None,
        qty=None,
        unit_price=None,
        line_total=None,
    ):
        query = """
        INSERT INTO invoice_items (
            invoice_id,
            item_type,
            item_id,
            description,
            qty,
            unit_price,
            line_total
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            invoice_id,
            item_type,
            item_id,
            description,
            qty,
            unit_price,
            line_total,
        )

        return self.db.insert_and_get_id(query, params)