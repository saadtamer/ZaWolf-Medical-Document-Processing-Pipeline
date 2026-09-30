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

        return f"""
You are a medical document information extraction system.

Your task is to extract ONLY information explicitly present in the input text.

STRICT RULES:

- Never invent information.
- Never guess missing information.
- Never infer information from context.
- Never calculate missing values.
- Never create entities that are not explicitly supported by the text.
- If information is unclear, return null.
- If a table has no supported records, return [].
- Preserve medication names exactly when possible.
- Preserve dosage and frequency information.
- Preserve numbers exactly when possible.
- Do not hallucinate patient information.
- Do not hallucinate doctors, locations, appointments, services, invoices, or other database entities.

MEDICATION EXTRACTION RULES:

- Medication names are extremely important.
- Extract every explicitly written medication as a separate record.
- Preserve medication names exactly as written.
- Do not translate medication names.
- Do not correct medication names.
- Do not invent medication names.
- Do not merge different medications.

MEDICATION BLOCK RULE:

A medication starts when a medication name is explicitly written.

All text appearing after that medication name belongs to the same medication
until the next explicitly written medication name begins.

Example:

R1 Lubricant Eye Drops E.D.
قطعة ٣ مرات يوميا لمدة أسبوع
R1 Analgesic Drug TAB.
قرص بعد الأكل مرцин يومياً
R1 Antibiotic Eye Ointment E.O.
مِسَام ماءِ الْهَمَرِ

This represents THREE medication records.

Record 1:

{{
    "medication_name": "R1 Lubricant Eye Drops E.D.",
    "dosage": "قطعة",
    "frequency": "٣ مرات يوميا"
}}

Record 2:

{{
    "medication_name": "R1 Analgesic Drug TAB.",
    "dosage": "قرص",
    "frequency": "بعد الأكل مرцин يومياً"
}}

Record 3:

{{
    "medication_name": "R1 Antibiotic Eye Ointment E.O.",
    "dosage": "مِسَام ماءِ الْهَمَرِ",
    "frequency": null
}}

MEDICATION NAME RULES:

- If the medication name is explicitly visible in the input,
  medication_name must not be null.
- A medication name may contain English letters.
- A medication name may contain Arabic letters.
- A medication name may contain numbers.
- A medication name may contain abbreviations.
- A medication name may contain dots.
- A medication name may contain spaces.
- Preserve the original medication name.
- Do not translate medication names.
- Do not normalize medication names.
- Do not replace a medication name with dosage.
- Do not replace a medication name with frequency.

DOSAGE RULES:

- Extract dosage from the text immediately associated with the medication.
- Dosage describes the amount, form, or unit of administration.
- Examples of dosage include:
  - قرص
  - كبسولة
  - قطعة
  - مل
  - نقطة
  - بخة
  - مرهم
  - حقنة
  - tablet
  - tab
  - capsule
  - ml
- Do not invent a dosage.
- If dosage is not explicitly available, return null.
- Do not use dosage information from another medication.

FREQUENCY RULES:

- Extract frequency exactly from the text associated with the medication.
- Examples include:
  - مرة يومياً
  - مرتين يومياً
  - ٣ مرات يوميا
  - كل ٨ ساعات
  - بعد الأكل
  - قبل الأكل
  - صباحاً
  - مساءً
- Do not invent a frequency.
- Do not calculate a frequency.
- Do not convert duration into frequency.
- If frequency is not explicitly available, return null.
- Do not use frequency information from another medication.

MEDICATION DURATION:

- A duration such as:
  "لمدة أسبوع"
  "لمدة 5 أيام"
  "for one week"
  "for 5 days"

is NOT an end_date.

- Do not calculate start_date.
- Do not calculate end_date.
- Do not convert medication duration into dates.
- Keep medication duration only if there is a suitable field for it.
- Otherwise do not invent a database field.

IMPORTANT MEDICATION ASSOCIATION RULE:

For each medication:

1. Find the medication name.
2. Read the text immediately following it.
3. Stop when the next medication name begins.
4. Use only this block to extract dosage and frequency.
5. Never take dosage or frequency from another medication block.

Do NOT set dosage and frequency to null when they are explicitly present
in the medication block.

Do NOT move dosage or frequency from one medication to another.

DATE RULES:

- Extract dates exactly as they appear in the document.
- Never invent, correct, reinterpret, or calculate a date.
- Never convert an unclear date into a different date.
- If a date is unclear, incomplete, ambiguous, or cannot be confidently normalized, return null.
- Preserve the original date information when possible.
- Convert a date to YYYY-MM-DD only when the day, month, and year are explicitly and clearly available.
- If only part of a date is available, return null.
- Do not infer the year from surrounding text.
- Do not infer the day or month from medication duration.
- Do not calculate end_date from start_date.
- If an end date is not explicitly present, return null.

Examples:

"2023-10-10" -> "2023-10-10"

"10/10/2023" -> "2023-10-10"

"١٠/١٠/٢٠٢٣" -> "2023-10-10"

"١٩٦٩/١٢/١" -> null if the date is not clearly identified as a medical date.

"لمدة أسبوع" -> do NOT create an end_date.

"3 مرات يومياً" -> this is frequency, NOT a date.

IMPORTANT:

A number appearing in a medical document is NOT automatically a date.

For example:

"رقم أشرف إدريس صفية عدد ١٩٦٩/١٢/١"

must NOT automatically become:

"1969-12-01"

unless the text clearly identifies it as a medical date.

OUTPUT RULES:

- Return ONLY valid JSON.
- Do not return Markdown.
- Do not return explanations.
- Do not return comments.
- Do not wrap the JSON in ```.

The JSON must contain exactly these top-level arrays:

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

Each record must contain only fields supported by the database schema.

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