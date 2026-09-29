from src.database.payment_repository import PaymentRepository


repository = PaymentRepository()

payment_id = repository.create(
    invoice_id=1,
    amount=1400.00,
    method="Cash",
    paid_at="2026-09-25 10:35:00",
    reference="PAY-001",
)

print(f"Payment created successfully. ID: {payment_id}")