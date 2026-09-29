from src.database.invoice_item_repository import InvoiceItemRepository


repository = InvoiceItemRepository()

item_id = repository.create(
    invoice_id=1,
    item_type="Service",
    item_id=1,
    description="Botox Treatment",
    qty=1,
    unit_price=1500.00,
    line_total=1500.00,
)

print(f"Invoice item created successfully. ID: {item_id}")