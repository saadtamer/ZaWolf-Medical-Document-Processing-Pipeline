from pathlib import Path

import pymupdf as fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import MAX_BATCH_TEXT_SIZE
from src.utils import get_dynamic_batch_limit


def detect_pdf_type(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF file.")

    document = fitz.open(file_path)

    try:
        text_length = sum(
            len(page.get_text("text").strip())
            for page in document
        )
    finally:
        document.close()

    pdf_type = "digital" if text_length > 0 else "scanned"

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "pdf_type": pdf_type,
        "text_length": text_length
    }


def extract_pdf_pages(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF file.")

    document = fitz.open(file_path)

    try:
        batch = []
        batch_size_bytes = 0
        batch_text_size = 0

        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()

            if not page_text:
                continue

            page_size_bytes = len(page_text.encode("utf-8"))
            page_text_size = len(page_text)

            memory_limit = get_dynamic_batch_limit()
            memory_budget = memory_limit["memory_budget_bytes"]

            exceeds_text_limit = (
                batch_text_size + page_text_size > MAX_BATCH_TEXT_SIZE
            )

            exceeds_memory_limit = (
                batch_size_bytes + page_size_bytes > memory_budget
            )

            if batch and (exceeds_text_limit or exceeds_memory_limit):
                yield batch

                batch = []
                batch_size_bytes = 0
                batch_text_size = 0

            batch.append({
                "file_name": file_path.name,
                "file_type": "pdf",
                "source_type": "page",
                "source_number": page_number,
                "text": page_text,
                "text_length": page_text_size
            })

            batch_size_bytes += page_size_bytes
            batch_text_size += page_text_size

        if batch:
            yield batch

    finally:
        document.close()


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=300,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


def create_contextual_chunks(page_batch, file_name):
    chunks = []

    page_texts = [
        page_data["text"]
        for page_data in page_batch
        if page_data["text"]
    ]

    if not page_texts:
        return chunks

    combined_text = "\n\n".join(page_texts)

    page_chunks = text_splitter.split_text(
        combined_text
    )

    for chunk_index, chunk_text in enumerate(
        page_chunks,
        start=1
    ):
        chunks.append({
            "file_name": file_name,
            "chunk_index": chunk_index,
            "text": chunk_text,
            "text_length": len(chunk_text)
        })

    return chunks


def process_pdf_to_chunks(file_path):
    for page_batch in extract_pdf_pages(file_path):
        yield create_contextual_chunks(
            page_batch,
            Path(file_path).name
        )


def convert_pdf_to_images(file_path, output_dir):
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file is not a PDF file.")

    output_dir.mkdir(parents=True, exist_ok=True)

    document = fitz.open(file_path)

    try:
        for page_number, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1, 1),
                alpha=False
            )

            image_path = (
                output_dir /
                f"{file_path.stem}_page_{page_number}.png"
            )

            pixmap.save(str(image_path))

            yield {
                "file_name": file_path.name,
                "page_number": page_number,
                "image_path": str(image_path)
            }

    finally:
        document.close()