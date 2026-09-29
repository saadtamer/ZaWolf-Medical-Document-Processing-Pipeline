from src.database.mapper import DatabaseMapper


def main():
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

        "appointments": [
            {
                "client_name": "Ahmed Ali",
                "staff_name": "Dr. Ahmed Hassan",
                "location_name": "Main Clinic",
                "service_name": "Botox",
                "room": "Room 1",
                "start_at": "2026-09-25 10:00:00",
                "end_at": "2026-09-25 10:30:00",
                "status": "Scheduled",
                "notes": "Full relational test",
            }
        ],

        "treatment_records": [
            {
                "product_name": "Botox 100U",
                "units": 40,
                "lot_number": "LOT-TEST-001",
                "expiry_date": "2027-12-31",
                "area": "Forehead",
                "injection_sites": "Frontalis",
                "depth": "Intramuscular",
                "device_settings": None,
                "skin_response": "Normal",
                "aftercare": "Follow standard aftercare instructions",
            }
        ],

        "invoices": [
            {
                "issue_date": "2026-09-25",
                "subtotal": 1500,
                "discount": 0,
                "tax": 0,
                "total": 1500,
                "status": "Paid",
            }
        ],

        "invoice_items": [
            {
                "item_type": "Service",
                "item_id": None,
                "description": "Botox",
                "qty": 1,
                "unit_price": 1500,
                "line_total": 1500,
            }
        ],

        "payments": [
            {
                "amount": 1500,
                "method": "Cash",
                "paid_at": "2026-09-25 10:30:00",
                "reference": "TEST-001",
            }
        ],
    }

    mapper = DatabaseMapper()
    result = mapper.save(data)

    print("FULL RELATIONAL TEST PASSED")
    print(result)


if __name__ == "__main__":
    main()