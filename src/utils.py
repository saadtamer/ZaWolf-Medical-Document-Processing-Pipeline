import psutil

from config.settings import BATCH_MEMORY_SAFETY_RATIO, MAX_BATCH_TEXT_SIZE
from langchain_text_splitters import RecursiveCharacterTextSplitter


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


def get_dynamic_batch_limit():
    memory = psutil.virtual_memory()

    available_bytes = memory.available
    memory_budget = int(
        available_bytes * BATCH_MEMORY_SAFETY_RATIO
    )

    return {
        "available_bytes": available_bytes,
        "memory_budget_bytes": memory_budget
    }


def batch_text_units(text_units):
    batch = []
    batch_size_bytes = 0
    batch_text_size = 0

    for unit in text_units:
        text = unit["text"]

        unit_size_bytes = len(text.encode("utf-8"))
        unit_text_size = len(text)

        memory_limit = get_dynamic_batch_limit()
        memory_budget = memory_limit["memory_budget_bytes"]

        exceeds_text_limit = (
            batch_text_size + unit_text_size > MAX_BATCH_TEXT_SIZE
        )

        exceeds_memory_limit = (
            batch_size_bytes + unit_size_bytes > memory_budget
        )

        if batch and (
            exceeds_text_limit or exceeds_memory_limit
        ):
            yield batch

            batch = []
            batch_size_bytes = 0
            batch_text_size = 0

        batch.append(unit)

        batch_size_bytes += unit_size_bytes
        batch_text_size += unit_text_size

    if batch:
        yield batch


def create_text_chunks(text_batch, file_name):
    chunks = []

    combined_text = "\n\n".join(
        unit["text"]
        for unit in text_batch
        if unit["text"]
    )

    if not combined_text:
        return chunks

    text_chunks = text_splitter.split_text(
        combined_text
    )

    for chunk_index, chunk_text in enumerate(
        text_chunks,
        start=1
    ):
        chunks.append({
            "file_name": file_name,
            "chunk_index": chunk_index,
            "text": chunk_text,
            "text_length": len(chunk_text)
        })

    return chunks


def process_text_units(text_units, file_name):
    for text_batch in batch_text_units(text_units):
        yield create_text_chunks(
            text_batch,
            file_name
        )

def create_content_record(
    file_name,
    file_type,
    content,
    source_type=None,
    source_number=None
):
    return {
        "file_name": file_name,
        "file_type": file_type,
        "source_type": source_type,
        "source_number": source_number,
        "content_type": "text",
        "content": content
    }        