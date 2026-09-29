from src.database.invoice_repository import InvoiceRepository


repository = InvoiceRepository()

invoice_id = repository.create(
    client_id=6,
    appointment_id=1,
    issue_date="2026-09-25",
    subtotal=1500.00,
    discount=100.00,
    tax=0.00,
    total=1400.00,
    status="Unpaid",
)

print(f"Invoice created successfully. ID: {invoice_id}")