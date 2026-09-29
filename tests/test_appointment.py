from src.database.appointment_repository import AppointmentRepository
from src.database.relation_resolver import RelationResolver


resolver = RelationResolver()
repository = AppointmentRepository()

client_id = resolver.find_client({
    "first_name": "Ahmed",
    "last_name": "Ali",
    "mobile": "01012345678",
})

staff_id = resolver.find_staff("Dr. Ahmed Hassan")
location_id = resolver.find_location("Main Clinic")
service_id = resolver.find_service("Botox")

appointment_id = repository.create(
    client_id=client_id,
    staff_id=staff_id,
    location_id=location_id,
    service_id=service_id,
    room="Room 1",
    start_at="2026-09-25 10:00:00",
    end_at="2026-09-25 10:30:00",
    status="Scheduled",
    notes="Test appointment",
)

print(f"Appointment created successfully. ID: {appointment_id}")