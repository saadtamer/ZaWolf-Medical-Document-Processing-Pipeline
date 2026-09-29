from src.database.client_package_repository import ClientPackageRepository


repository = ClientPackageRepository()

client_package_id = repository.create(
    client_id=6,
    package_id=1,
    remaining_sessions=3,
    expires_at="2026-12-24",
)

print(
    f"Client package created successfully. ID: {client_package_id}"
)