from src.database.consent_repository import ConsentRepository


repository = ConsentRepository()

consent_id = repository.create(
    client_id=6,
    appointment_id=1,
    consent_type="Treatment Consent",
    signed_at="2026-09-25 09:45:00",
    file_ref="consents/ahmed/treatment_consent.pdf",
)

print(f"Consent created successfully. ID: {consent_id}")