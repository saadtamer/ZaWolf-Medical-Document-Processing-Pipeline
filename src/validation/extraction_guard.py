class ExtractionGuard:
    def apply(self, data, text):
        self._guard_prescription_entities(data, text)
        self._guard_empty_entities(data)
        return data

    def _guard_prescription_entities(self, data, text):
        text_lower = text.lower()

        prescription_keywords = [
            "prescription",
            "prescription:",
            "rx",
            "دواء",
            "ادوية",
            "دواء",
            "روشتة",
            "علاج",
            "مرات يوميا",
            "مرة يوميا",
            "بعد الأكل",
            "قبل الأكل",
            "قطرة",
            "قرص",
            "كبسولة",
            "مرهم",
        ]

        is_prescription = any(
            keyword in text_lower
            for keyword in prescription_keywords
        )

        if not is_prescription:
            return

        allowed_tables = {
            "medications",
        }

        protected_tables = [
            "locations",
            "staff",
            "clients",
            "medical_history",
            "vitals",
            "lab_results",
            "services",
            "appointments",
            "treatment_records",
            "consents",
            "photos",
            "invoices",
            "invoice_items",
            "payments",
            "packages",
            "client_packages",
            "products",
        ]

        for table in protected_tables:
            if table not in allowed_tables:
                data[table] = []

    def _guard_empty_entities(self, data):
        for table, records in data.items():
            if not isinstance(records, list):
                continue

            cleaned_records = []

            for record in records:
                if not isinstance(record, dict):
                    continue

                if any(
                    value is not None and value != ""
                    for value in record.values()
                ):
                    cleaned_records.append(record)

            data[table] = cleaned_records