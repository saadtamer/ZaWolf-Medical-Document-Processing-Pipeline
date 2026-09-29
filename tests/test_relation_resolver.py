from src.database.relation_resolver import RelationResolver


resolver = RelationResolver()

client_id = resolver.find_client({
    "first_name": "Ahmed",
    "last_name": "Ali",
    "mobile": "01012345678",
})

print(f"Resolved client ID: {client_id}")