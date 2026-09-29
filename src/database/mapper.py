from src.database.database import Database
from src.database.repository import Repository
from src.database.relation_resolver import RelationResolver


class DatabaseMapper:
    def __init__(self):
        self.db = Database()
        self.resolver = RelationResolver()

        tables = [
            "locations",
            "staff",
            "clients",
            "medical_history",
            "vitals",
            "lab_results",
            "medications",
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
            "source_documents",
        ]

        self.repositories = {
            table: Repository(table)
            for table in tables
        }

    def save(self, data):
        connection = self.db.connect()
        cursor = connection.cursor()

        inserted = {
            table: []
            for table in self.repositories
        }

        try:
            self._insert_simple(
                "locations",
                data,
                cursor,
                inserted,
            )

            self._insert_staff(
                data,
                cursor,
                inserted,
            )

            client_ids = self._insert_clients(
                data,
                cursor,
                inserted,
            )

            self._insert_medical_data(
                data,
                client_ids,
                cursor,
                inserted,
            )

            self._insert_simple(
                "services",
                data,
                cursor,
                inserted,
            )

            self._insert_simple(
                "packages",
                data,
                cursor,
                inserted,
            )

            self._insert_simple(
                "products",
                data,
                cursor,
                inserted,
            )

            self._insert_appointments(
                data,
                cursor,
                inserted,
            )

            self._insert_treatments(
                data,
                cursor,
                inserted,
            )

            self._insert_consents(
                data,
                cursor,
                inserted,
            )

            self._insert_photos(
                data,
                cursor,
                inserted,
            )

            self._insert_invoices(
                data,
                cursor,
                inserted,
            )

            self._insert_invoice_items(
                data,
                cursor,
                inserted,
            )

            self._insert_payments(
                data,
                cursor,
                inserted,
            )

            self._insert_client_packages(
                data,
                client_ids,
                cursor,
                inserted,
            )

            self._insert_simple(
                "source_documents",
                data,
                cursor,
                inserted,
            )

            connection.commit()

            return inserted

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    def _insert_simple(
        self,
        table,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(table, []):
            record_id = self.repositories[table].insert(
                record,
                cursor,
            )

            inserted[table].append(record_id)

    def _insert_staff(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get("staff", []):
            record = record.copy()

            location_name = record.pop(
                "location_name",
                None,
            )

            if location_name:
                location_id = self.resolver.find_location(
                    location_name,
                    cursor,
                )

                if location_id is None:
                    raise ValueError(
                        f"Location not found: {location_name}"
                    )

                record["location_id"] = location_id

            record_id = self.repositories["staff"].insert(
                record,
                cursor,
            )

            inserted["staff"].append(record_id)

    def _insert_clients(
        self,
        data,
        cursor,
        inserted,
    ):
        client_ids = []

        for record in data.get("clients", []):
            record_id = self.repositories["clients"].insert(
                record,
                cursor,
            )

            client_ids.append(record_id)
            inserted["clients"].append(record_id)

        return client_ids

    def _insert_medical_data(
        self,
        data,
        client_ids,
        cursor,
        inserted,
    ):
        client_id = client_ids[0] if client_ids else None

        for table in [
            "medical_history",
            "vitals",
            "lab_results",
            "medications",
        ]:
            for record in data.get(table, []):
                if table != "medications" and client_id is None:
                    continue

                record = record.copy()

                if client_id is not None:
                    record["client_id"] = client_id

                record_id = self.repositories[table].insert(
                    record,
                    cursor,
                )

                inserted[table].append(record_id)

    def _insert_appointments(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get("appointments", []):
            record = record.copy()

            client_name = record.pop(
                "client_name",
                None,
            )

            staff_name = record.pop(
                "staff_name",
                None,
            )

            location_name = record.pop(
                "location_name",
                None,
            )

            service_name = record.pop(
                "service_name",
                None,
            )

            if client_name:
                if inserted["clients"]:
                    record["client_id"] = inserted["clients"][0]

                else:
                    parts = client_name.split(maxsplit=1)

                    client = {
                        "first_name": parts[0],
                        "last_name": (
                            parts[1]
                            if len(parts) > 1
                            else ""
                        ),
                        "mobile": None,
                    }

                    client_id = self.resolver.find_client(
                        client,
                        cursor,
                    )

                    if client_id is None:
                        raise ValueError(
                            f"Client not found: {client_name}"
                        )

                    record["client_id"] = client_id

            elif inserted["clients"]:
                record["client_id"] = inserted["clients"][0]

            if staff_name:
                staff_id = self.resolver.find_staff(
                    staff_name,
                    cursor,
                )

                if staff_id is None:
                    raise ValueError(
                        f"Staff not found: {staff_name}"
                    )

                record["staff_id"] = staff_id

            if location_name:
                location_id = self.resolver.find_location(
                    location_name,
                    cursor,
                )

                if location_id is None:
                    raise ValueError(
                        f"Location not found: {location_name}"
                    )

                record["location_id"] = location_id

            if service_name:
                service_id = self.resolver.find_service(
                    service_name,
                    cursor,
                )

                if service_id is None:
                    raise ValueError(
                        f"Service not found: {service_name}"
                    )

                record["service_id"] = service_id

            record_id = self.repositories[
                "appointments"
            ].insert(
                record,
                cursor,
            )

            inserted["appointments"].append(
                record_id
            )

    def _insert_treatments(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "treatment_records",
            [],
        ):
            record = record.copy()

            product_name = record.pop(
                "product_name",
                None,
            )

            if product_name:
                product_id = self.resolver.find_product(
                    product_name,
                    cursor,
                )

                if product_id is None:
                    raise ValueError(
                        f"Product not found: {product_name}"
                    )

                record["product_id"] = product_id

            if (
                "appointment_id" not in record
                and inserted["appointments"]
            ):
                record["appointment_id"] = (
                    inserted["appointments"][0]
                )

            record_id = self.repositories[
                "treatment_records"
            ].insert(
                record,
                cursor,
            )

            inserted["treatment_records"].append(
                record_id
            )

    def _insert_consents(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "consents",
            [],
        ):
            record = record.copy()

            record.pop(
                "appointment_id",
                None,
            )

            if inserted["clients"]:
                record["client_id"] = (
                    inserted["clients"][0]
                )

            record_id = self.repositories[
                "consents"
            ].insert(
                record,
                cursor,
            )

            inserted["consents"].append(
                record_id
            )

    def _insert_photos(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "photos",
            [],
        ):
            record = record.copy()

            record.pop(
                "treatment_id",
                None,
            )

            if inserted["clients"]:
                record["client_id"] = (
                    inserted["clients"][0]
                )

            if inserted["treatment_records"]:
                record["treatment_id"] = (
                    inserted["treatment_records"][0]
                )

            record_id = self.repositories[
                "photos"
            ].insert(
                record,
                cursor,
            )

            inserted["photos"].append(
                record_id
            )

    def _insert_invoices(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "invoices",
            [],
        ):
            record = record.copy()

            if inserted["clients"]:
                record["client_id"] = (
                    inserted["clients"][0]
                )

            if (
                "appointment_id" not in record
                and inserted["appointments"]
            ):
                record["appointment_id"] = (
                    inserted["appointments"][0]
                )

            record_id = self.repositories[
                "invoices"
            ].insert(
                record,
                cursor,
            )

            inserted["invoices"].append(
                record_id
            )

    def _insert_invoice_items(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "invoice_items",
            [],
        ):
            record = record.copy()

            if not inserted["invoices"]:
                raise ValueError(
                    "Cannot insert invoice item without invoice"
                )

            record.pop(
                "invoice_id",
                None,
            )

            record["invoice_id"] = (
                inserted["invoices"][0]
            )

            record_id = self.repositories[
                "invoice_items"
            ].insert(
                record,
                cursor,
            )

            inserted["invoice_items"].append(
                record_id
            )

    def _insert_payments(
        self,
        data,
        cursor,
        inserted,
    ):
        for record in data.get(
            "payments",
            [],
        ):
            record = record.copy()

            if not inserted["invoices"]:
                raise ValueError(
                    "Cannot insert payment without invoice"
                )

            record.pop(
                "invoice_id",
                None,
            )

            record["invoice_id"] = (
                inserted["invoices"][0]
            )

            record_id = self.repositories[
                "payments"
            ].insert(
                record,
                cursor,
            )

            inserted["payments"].append(
                record_id
            )

    def _insert_client_packages(
        self,
        data,
        client_ids,
        cursor,
        inserted,
    ):
        if not client_ids:
            return

        client_id = client_ids[0]

        for record in data.get(
            "client_packages",
            [],
        ):
            record = record.copy()

            package_name = record.pop(
                "package_name",
                None,
            )

            if not package_name:
                raise ValueError(
                    "client_package requires package_name"
                )

            package_id = self.resolver.find_package(
                package_name,
                cursor,
            )

            if package_id is None:
                raise ValueError(
                    f"Package not found: {package_name}"
                )

            record["client_id"] = client_id
            record["package_id"] = package_id

            record_id = self.repositories[
                "client_packages"
            ].insert(
                record,
                cursor,
            )

            inserted["client_packages"].append(
                record_id
            )