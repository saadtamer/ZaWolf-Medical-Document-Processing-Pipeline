from src.database.client_repository import ClientRepository


repository = ClientRepository()

client = {
    "first_name": "Ahmed",
    "last_name": "Ali",
    "dob": "1985-03-15",
    "gender": "Male",
    "mobile": "01012345678",
    "email": None,
    "address": None,
    "lead_source": None,
    "medical_alerts": None,
    "opt_in_sms": None,
}

client_id = repository.create(client)

print(f"Client inserted successfully. ID: {client_id}")