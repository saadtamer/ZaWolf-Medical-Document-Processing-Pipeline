from src.database.package_repository import PackageRepository


repository = PackageRepository()

package_id = repository.create(
    name="Botox Package",
    sessions_count=3,
    price=4000.00,
    validity_days=90,
)

print(f"Package created successfully. ID: {package_id}")