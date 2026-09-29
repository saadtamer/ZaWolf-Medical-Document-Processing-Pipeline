from src.database.mapper import DatabaseMapper


def main():
    data = {
        "clients": [
            {
                "first_name": "Rollback",
                "last_name": "Test",
                "dob": "1990-01-01",
                "gender": "Male",
                "mobile": "01199999999",
                "email": None,
                "address": None,
                "lead_source": None,
                "medical_alerts": None,
                "opt_in_sms": None,
            }
        ],
        "appointments": [
            {
                "client_name": "Rollback Test",
                "staff_name": "Dr. Ahmed Hassan",
                "location_name": "Main Clinic",
                "service_name": "Botox",
                "room": "Rollback Room",
                "start_at": "2026-09-25 12:00:00",
                "end_at": "2026-09-25 12:30:00",
                "status": "Scheduled",
                "notes": "Rollback test",
            }
        ],
        "treatment_records": [
            {
                "product_name": "PRODUCT_DOES_NOT_EXIST",
                "units": 10,
                "lot_number": "ROLLBACK-001",
                "expiry_date": "2027-12-31",
                "area": "Test",
                "injection_sites": "Test",
                "depth": "Test",
                "device_settings": None,
                "skin_response": "Normal",
                "aftercare": None,
            }
        ],
    }

    mapper = DatabaseMapper()

    try:
        mapper.save(data)
        raise AssertionError(
            "Rollback test failed: save unexpectedly succeeded"
        )

    except ValueError as error:
        print("EXPECTED ERROR:")
        print(error)
        print("ROLLBACK TEST PASSED")


if __name__ == "__main__":
    main()