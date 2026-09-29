from src.database.treatment_repository import TreatmentRepository


repository = TreatmentRepository()

treatment_id = repository.create(
    appointment_id=1,
    product_id=1,
    units=40,
    lot_number="LOT-001",
    expiry_date="2027-12-31",
    area="Forehead",
    injection_sites="Frontalis",
    depth="Intramuscular",
    device_settings=None,
    skin_response="Normal",
    aftercare="Avoid rubbing the treated area for 4 hours",
)

print(f"Treatment created successfully. ID: {treatment_id}")