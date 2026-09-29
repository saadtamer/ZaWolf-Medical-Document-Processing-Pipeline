from src.database.database import Database


class SourceDocumentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        file_name,
        doc_type=None,
        ocr_text=None,
        llm_json=None,
        confidence=None,
        review_status=None,
    ):
        query = """
        INSERT INTO source_documents (
            file_name,
            doc_type,
            ocr_text,
            llm_json,
            confidence,
            review_status
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?)
        """

        params = (
            file_name,
            doc_type,
            ocr_text,
            llm_json,
            confidence,
            review_status,
        )

        return self.db.insert_and_get_id(query, params)