from src.database.mapper import DatabaseMapper


mapper = DatabaseMapper()

data = {
    "clients": [
        {
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
    ],
    "medical_history": [
        {
            "type": "Diagnosis",
            "name": "Migraine",
            "notes": "Patient reports headache for 3 days.",
            "recorded_at": "2026-09-20",
        }
    ],
    "vitals": [
        {
            "blood_pressure": "120/80",
            "heart_rate": 75,
            "temperature": 37.2,
            "weight": 82,
            "recorded_at": "2026-09-20",
        }
    ],
    "lab_results": [
        {
            "test_name": "Hemoglobin",
            "value": 13.5,
            "unit": "g/dL",
            "reference_range": "12 - 16 g/dL",
            "test_date": "2026-09-20",
        }
    ],
    "medications": [
        {
            "medication_name": "Metformin",
            "dosage": "500 mg",
            "frequency": "Twice daily",
            "start_date": None,
            "end_date": None,
        }
    ],
}

result = mapper.save(data)

print(result)