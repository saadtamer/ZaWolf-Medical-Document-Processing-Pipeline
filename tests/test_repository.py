from src.database.repository import Repository


repository = Repository("clients")

client = {
    "first_name": "Sara",
    "last_name": "Mohamed",
    "dob": "1998-07-10",
    "gender": "Female",
    "mobile": "01123456789",
    "email": "sara@example.com",
    "address": "Cairo",
    "lead_source": "Website",
    "medical_alerts": None,
    "opt_in_sms": True,
}

client_id = repository.insert(client)

print(f"Generic insert successful. ID: {client_id}")