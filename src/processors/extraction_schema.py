from datetime import datetime


def create_unified_extraction(
    file_name,
    file_type,
    content_type,
    sources,
    metadata=None
):
    return {
        "file": {
            "name": file_name,
            "type": file_type
        },
        "content_type": content_type,
        "sources": sources,
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat()
    }


def create_text_source(
    source_number,
    text,
    source_type="text",
    language=None,
    confidence=None,
    ocr_engine=None
):
    source = {
        "source_type": source_type,
        "source_number": source_number,
        "raw_text": text
    }

    if language is not None:
        source["language"] = language

    if confidence is not None:
        source["confidence"] = confidence

    if ocr_engine is not None:
        source["ocr_engine"] = ocr_engine

    return source


def create_structured_source(
    source_number,
    data,
    source_type="structured"
):
    return {
        "source_type": source_type,
        "source_number": source_number,
        "raw_data": data
    }