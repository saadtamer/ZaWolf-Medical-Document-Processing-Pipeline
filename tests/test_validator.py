from src.validation.validator import DataValidator


def main():
    validator = DataValidator()

    valid_data = {
        "locations": [],
        "staff": [],
        "clients": [
            {
                "first_name": "Ahmed",
                "last_name": "Ali",
                "dob": "1985-03-15",
                "gender": "Male",
                "mobile": "01012345678"
            }
        ],
        "medical_history": [
            {
                "type": "Diagnosis",
                "name": "Migraine",
                "notes": "Patient reports headache for 3 days.",
                "recorded_at": "2026-09-20"
            }
        ],
        "vitals": [
            {
                "blood_pressure": "120/80",
                "heart_rate": 75,
                "temperature": 37.2,
                "weight": 82,
                "recorded_at": "2026-09-20"
            }
        ],
        "lab_results": [
            {
                "test_name": "Hemoglobin",
                "value": 13.5,
                "unit": "g/dL",
                "reference_range": "12 - 16 g/dL",
                "test_date": "2026-09-20"
            }
        ],
        "medications": [
            {
                "medication_name": "Metformin",
                "dosage": "500 mg",
                "frequency": "Twice daily"
            }
        ],
        "services": [],
        "appointments": [],
        "treatment_records": [],
        "consents": [],
        "photos": [],
        "invoices": [],
        "invoice_items": [],
        "payments": [],
        "packages": [],
        "client_packages": [],
        "products": [],
        "source_documents": []
    }

    result = validator.validate(valid_data)

    print("\nVALIDATION RESULT:\n")
    print(result)


if __name__ == "__main__":
    main()