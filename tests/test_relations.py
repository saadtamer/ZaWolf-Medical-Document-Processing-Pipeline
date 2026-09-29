from src.database.relation_resolver import RelationResolver


resolver = RelationResolver()

client_id = resolver.find_client({
    "first_name": "Ahmed",
    "last_name": "Ali",
    "mobile": "01012345678",
})

staff_id = resolver.find_staff("Dr. Ahmed Hassan")
location_id = resolver.find_location("Main Clinic")
service_id = resolver.find_service("Botox")

print(f"client_id: {client_id}")
print(f"staff_id: {staff_id}")
print(f"location_id: {location_id}")
print(f"service_id: {service_id}")