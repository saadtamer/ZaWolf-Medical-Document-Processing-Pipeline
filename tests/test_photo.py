from src.database.photo_repository import PhotoRepository


repository = PhotoRepository()

photo_id = repository.create(
    client_id=6,
    treatment_id=1,
    photo_type="Before",
    taken_at="2026-09-25 09:50:00",
    file_ref="photos/ahmed/before_001.jpg",
)

print(f"Photo created successfully. ID: {photo_id}")