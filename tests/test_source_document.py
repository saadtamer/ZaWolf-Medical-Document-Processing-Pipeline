from src.database.source_document_repository import SourceDocumentRepository


repository = SourceDocumentRepository()

document_id = repository.create(
    file_name="patient_record.pdf",
    doc_type="medical_document",
    ocr_text="Patient: Ahmed Ali",
    llm_json='{"clients": [{"first_name": "Ahmed", "last_name": "Ali"}]}',
    confidence=0.95,
    review_status="approved",
)

print(f"Source document created successfully. ID: {document_id}")