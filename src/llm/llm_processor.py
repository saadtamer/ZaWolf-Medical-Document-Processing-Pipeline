import json
from datetime import datetime

from src.llm.local_llm import LocalLLM
from src.llm.llm_schema import LLMExtractionResult
from src.validation.extraction_guard import ExtractionGuard


class LLMProcessor:

    def __init__(
        self,
        model="qwen3:latest",
        base_url="http://localhost:11434",
        timeout=600,
    ):
        self.llm = LocalLLM(
            model=model,
            base_url=base_url,
            timeout=timeout,
        )

        self.guard = ExtractionGuard()

    def build_prompt(self, text):
        return f"""You are a clinical document information extraction system. Extract ONLY explicitly stated facts into the exact JSON schema below.

STRICT CONSTRAINTS:
- NEVER hallucinate, invent, or extrapolate unmentioned entities.
- If an entity or attribute is not explicitly in the text, return null (or [] for arrays).
- Never invent patient names, doctors, locations, appointments, diagnoses, or invoices.
- Dates: Use YYYY-MM-DD only when day, month, and year are clearly given; otherwise null. Do not convert durations (e.g. "لمدة أسبوع") into dates.
- Numbers: Preserve original values accurately.

MEDICATION EXTRACTION:
- Extract each explicitly named medication as a separate record. Preserve exact medication_name, dosage, and frequency.
- Only associate dosage and frequency appearing in the text immediately following the medication name.
- Do not mix attributes between different medications.

OUTPUT RULES:
Return ONLY valid JSON (no markdown fences, no conversational text, no comments). Schema:
{{
    "locations": [],
    "staff": [],
    "clients": [],
    "medical_history": [],
    "vitals": [],
    "lab_results": [],
    "medications": [],
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
}}

Each entity must contain only schema-supported fields (e.g. medications: medication_name, dosage, frequency; vitals: blood_pressure, heart_rate, temperature, weight; locations: name, address, phone).

INPUT TEXT:
{text}
"""

    def _parse_json(self, response_text):

        response_text = response_text.strip()

        if response_text.startswith("```"):

            lines = response_text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            response_text = "\n".join(lines).strip()

        try:
            return json.loads(response_text)

        except json.JSONDecodeError as error:

            raise ValueError(
                f"LLM returned invalid JSON: {error}"
            ) from error

    def _normalize_numeric_values(self, data):

        numeric_fields = {
            "clients": [
                "id",
            ],
            "vitals": [
                "weight",
                "height",
                "temperature",
                "heart_rate",
                "blood_pressure_systolic",
                "blood_pressure_diastolic",
                "oxygen_saturation",
            ],
            "lab_results": [
                "result_value",
                "reference_min",
                "reference_max",
            ],
            "invoices": [
                "subtotal",
                "discount",
                "tax",
                "total",
            ],
            "invoice_items": [
                "quantity",
                "unit_price",
                "total",
            ],
            "payments": [
                "amount",
            ],
        }

        for table, fields in numeric_fields.items():

            records = data.get(table, [])

            if not isinstance(records, list):
                continue

            for record in records:

                if not isinstance(record, dict):
                    continue

                for field in fields:

                    value = record.get(field)

                    if value is None:
                        continue

                    if isinstance(value, (int, float)):
                        continue

                    if not isinstance(value, str):
                        record[field] = None
                        continue

                    value = value.strip()

                    if value == "":
                        record[field] = None
                        continue

                    try:

                        if "." in value:
                            record[field] = float(value)
                        else:
                            record[field] = int(value)

                    except ValueError:

                        record[field] = None

        return data

    def _normalize_string_values(self, data):

        string_fields = {
            "locations": [
                "name",
                "address",
                "phone",
            ],
            "staff": [
                "first_name",
                "last_name",
                "role",
                "specialization",
                "phone",
                "email",
            ],
            "clients": [
                "first_name",
                "last_name",
                "gender",
                "phone",
                "email",
                "address",
            ],
            "medical_history": [
                "condition",
                "diagnosis",
                "notes",
            ],
            "vitals": [
                "blood_pressure",
                "notes",
            ],
            "lab_results": [
                "test_name",
                "result",
                "unit",
                "reference_range",
                "notes",
            ],
            "medications": [
                "medication_name",
                "dosage",
                "frequency",
            ],
            "services": [
                "name",
                "description",
            ],
            "appointments": [
                "status",
                "notes",
            ],
            "treatment_records": [
                "treatment_name",
                "description",
                "notes",
            ],
            "consents": [
                "consent_type",
                "status",
                "notes",
            ],
            "photos": [
                "file_path",
                "description",
            ],
            "invoices": [
                "invoice_number",
                "status",
                "notes",
            ],
            "invoice_items": [
                "description",
            ],
            "payments": [
                "payment_method",
                "status",
                "transaction_reference",
            ],
            "packages": [
                "name",
                "description",
            ],
            "client_packages": [
                "status",
            ],
            "products": [
                "name",
                "description",
                "category",
            ],
            "source_documents": [
                "file_name",
                "file_type",
                "file_path",
            ],
        }

        for table, fields in string_fields.items():

            records = data.get(table, [])

            if not isinstance(records, list):
                continue

            for record in records:

                if not isinstance(record, dict):
                    continue

                for field in fields:

                    value = record.get(field)

                    if value is None:
                        continue

                    if not isinstance(value, str):
                        record[field] = str(value)

        return data

    def _normalize_dates(self, data):

        date_fields = {
            "clients": [
                "dob",
            ],
            "medical_history": [
                "recorded_at",
            ],
            "vitals": [
                "recorded_at",
            ],
            "lab_results": [
                "test_date",
            ],
            "medications": [
                "start_date",
                "end_date",
            ],
            "invoices": [
                "issue_date",
            ],
            "treatment_records": [
                "expiry_date",
            ],
        }

        datetime_fields = {
            "appointments": [
                "start_at",
                "end_at",
            ],
            "consents": [
                "signed_at",
            ],
            "photos": [
                "taken_at",
            ],
            "payments": [
                "paid_at",
            ],
        }

        for table, fields in date_fields.items():

            records = data.get(table, [])

            if not isinstance(records, list):
                continue

            for record in records:

                if not isinstance(record, dict):
                    continue

                for field in fields:

                    value = record.get(field)

                    if value is None:
                        record[field] = None
                        continue

                    if not isinstance(value, str):
                        record[field] = None
                        continue

                    value = value.strip()

                    if value == "":
                        record[field] = None
                        continue

                    try:

                        parsed_date = datetime.strptime(
                            value,
                            "%Y-%m-%d",
                        )

                        record[field] = parsed_date.strftime(
                            "%Y-%m-%d"
                        )

                    except ValueError:

                        record[field] = None

        for table, fields in datetime_fields.items():

            records = data.get(table, [])

            if not isinstance(records, list):
                continue

            for record in records:

                if not isinstance(record, dict):
                    continue

                for field in fields:

                    value = record.get(field)

                    if value is None:
                        record[field] = None
                        continue

                    if not isinstance(value, str):
                        record[field] = None
                        continue

                    value = value.strip()

                    if value == "":
                        record[field] = None
                        continue

                    valid_formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d %H:%M",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M",
                    ]

                    normalized = None

                    for date_format in valid_formats:

                        try:

                            parsed_datetime = datetime.strptime(
                                value,
                                date_format,
                            )

                            normalized = parsed_datetime.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )

                            break

                        except ValueError:
                            continue

                    record[field] = normalized

        return data

    def process(self, text):

        prompt = self.build_prompt(text)

        raw_response = self.llm.generate(
            prompt
        )

        data = self._parse_json(
            raw_response
        )

        data = self._normalize_numeric_values(
            data
        )

        data = self._normalize_string_values(
            data
        )

        data = self._normalize_dates(
            data
        )

        data = self.guard.apply(
            data,
            text
        )

        validated = LLMExtractionResult.model_validate(
            data
        )

        return validated.model_dump()