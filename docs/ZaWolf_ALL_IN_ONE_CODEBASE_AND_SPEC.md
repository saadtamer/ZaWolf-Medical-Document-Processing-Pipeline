# ZaWolf System — ALL-IN-ONE MASTER CONTEXT & COMPLETE CODEBASE
## Complete Architecture, Invariants, and 100% Verbatim Source Code for All Modules
> **DIRECTIVE FOR LLM AGENTS:** You have the ENTIRE architecture AND the VERBATIM SOURCE CODE of every single file in the project within this single document. Do NOT ask the user for any source files or implementations. Everything is provided below.

```yaml
project_name: ZaWolf_project
project_root: 'E:\ZaWolf_project'
environment: Python 3.11.9, Windows, Microsoft SQL Server (ZaWolfDB), Ollama (qwen3), PyTorch (CUDA/CPU)
total_modules: 45
persistence: Single transaction atomic commit/rollback across 19 relational tables
```

## PART 1: CORE INVARIANTS & SYSTEM RULES

1. File type detection is strictly rule-based via file extensions (file_detector.py).
2. Routing is deterministic (router.py).
3. Scanned PDF pages are converted directly to images and enter the EXACT SAME Image/OCR pipeline as standard images.
4. Word, Excel, and CSV files NEVER pass through OCR.
5. Missing values are preserved as null. Raw extraction never performs domain cleaning.
6. The LLM must NEVER hallucinate or invent missing data or synthetic primary keys.
7. ExtractionGuard: If input is a prescription, zero out all 17 non-medication tables.
8. DatabaseMapper saves across all 19 tables in a single transaction with a single cursor; rollback on any failure.
9. RelationResolver matches clients by (first_name, last_name, mobile), staff by full_name, and location by name.

## PART 2: COMPLETE VERBATIM SOURCE CODE BY FILE

### File: `config/settings.py`
**Path:** `E:\ZaWolf_project\config\settings.py`
```python
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
IMAGE_PROCESSED_DIR = PROCESSED_DIR / "images"
PDF_IMAGES_DIR = PROCESSED_DIR / "pdf_images"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"


MAX_BATCH_TEXT_SIZE = 12000

BATCH_MEMORY_SAFETY_RATIO = 0.25


SUPPORTED_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
]


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".docx": "word",
}
```

### File: `src/ingestion/file_detector.py`
**Path:** `E:\ZaWolf_project\src\ingestion\file_detector.py`
```python
from pathlib import Path

from config.settings import INPUT_DIR, SUPPORTED_EXTENSIONS


def get_input_files():
    return [
        file_path
        for file_path in INPUT_DIR.iterdir()
        if file_path.is_file()
    ]


def detect_file_type(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = file_path.suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(extension)

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "extension": extension,
        "file_type": file_type or "unsupported",
        "supported": file_type is not None
    }
```

### File: `src/ingestion/router.py`
**Path:** `E:\ZaWolf_project\src\ingestion\router.py`
```python
def route_file(file_info):
    file_type = file_info["file_type"]

    routes = {
        "pdf": "pdf_pipeline",
        "image": "image_pipeline",
        "excel": "excel_pipeline",
        "csv": "csv_pipeline",
        "word": "word_pipeline"
    }

    return routes.get(file_type, "unsupported")
```

### File: `src/processors/pdf_processor.py`
**Path:** `E:\ZaWolf_project\src\processors\pdf_processor.py`
```python
from pathlib import Path

import fitz
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
```

### File: `src/processors/image_processor.py`
**Path:** `E:\ZaWolf_project\src\processors\image_processor.py`
```python
from pathlib import Path

from PIL import Image, ImageOps

from config.settings import (
    SUPPORTED_IMAGE_EXTENSIONS,
    IMAGE_PROCESSED_DIR
)


def load_and_validate_image(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            "The provided file is not a supported image format."
        )

    try:
        image = Image.open(file_path)
        image.load()
    except Exception as error:
        raise ValueError(
            f"Invalid or corrupted image: {error}"
        )

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "format": image.format,
        "mode": image.mode,
        "width": image.width,
        "height": image.height
    }


def preprocess_image(file_path, output_path=None):
    file_path = Path(file_path)

    image = Image.open(file_path)
    image.load()

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)

    if output_path is not None:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        image.save(output_path)

    return image


def process_image(file_path):
    file_path = Path(file_path)

    load_and_validate_image(file_path)

    output_path = (
        IMAGE_PROCESSED_DIR /
        f"{file_path.stem}_processed.png"
    )

    image = preprocess_image(
        file_path,
        output_path
    )

    return {
        "file_name": file_path.name,
        "file_type": "image",
        "content_type": "image",
        "original_path": str(file_path),
        "processed_path": str(output_path),
        "width": image.width,
        "height": image.height,
        "mode": image.mode
    }
```

### File: `src/processors/word_processor.py`
**Path:** `E:\ZaWolf_project\src\processors\word_processor.py`
```python
from pathlib import Path

from docx import Document

from src.utils import process_text_units


def extract_word_content(file_path):
    file_path = Path(file_path)

    if file_path.suffix.lower() != ".docx":
        raise ValueError(
            "The provided file is not a DOCX file."
        )

    document = Document(file_path)

    content = []

    for paragraph_number, paragraph in enumerate(
        document.paragraphs,
        start=1
    ):
        text = paragraph.text.strip()

        if text:
            content.append({
                "source_type": "paragraph",
                "source_number": paragraph_number,
                "text": text,
                "text_length": len(text)
            })

    for table_number, table in enumerate(
        document.tables,
        start=1
    ):
        rows = []

        for row in table.rows:
            cells = [
                cell.text.strip()
                for cell in row.cells
            ]

            if any(cells):
                rows.append(cells)

        if rows:
            table_text = "\n".join(
                " | ".join(row)
                for row in rows
            )

            content.append({
                "source_type": "table",
                "source_number": table_number,
                "text": table_text,
                "text_length": len(table_text)
            })

    return content


def process_word(file_path):
    file_path = Path(file_path)

    text_units = extract_word_content(file_path)

    yield from process_text_units(
        text_units,
        file_path.name
    )
```

### File: `src/processors/structured_processor.py`
**Path:** `E:\ZaWolf_project\src\processors\structured_processor.py`
```python
from pathlib import Path

import pandas as pd


def extract_structured_data(file_info):
    file_path = Path(file_info["file_path"])
    file_type = file_info["file_type"]

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_type == "csv":
        sheets = {
            "default": pd.read_csv(file_path)
        }

    elif file_type == "excel":
        sheets = pd.read_excel(
            file_path,
            sheet_name=None
        )

    else:
        raise ValueError(
            "The provided file is not an Excel or CSV file."
        )

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_type": file_type,
        "content_type": "structured",
        "sheets": sheets
    }
```

### File: `src/processors/extraction_schema.py`
**Path:** `E:\ZaWolf_project\src\processors\extraction_schema.py`
```python
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
```

### File: `src/ocr/device.py`
**Path:** `E:\ZaWolf_project\src\ocr\device.py`
```python
import torch


def get_device(preference="auto"):
    if preference == "cpu":
        return "cpu"

    if preference == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available.")
        return "cuda"

    return "cuda" if torch.cuda.is_available() else "cpu"
```

### File: `src/ocr/ocr_engine.py`
**Path:** `E:\ZaWolf_project\src\ocr\ocr_engine.py`
```python
import os

os.environ["FLAGS_enable_pir_api"] = "0"

from pathlib import Path
from paddleocr import PaddleOCR

from src.ocr.ocr_utils import (
    validate_image_path,
    parse_paddle_result,
    create_ocr_record
)


class OCREngine:

    def __init__(self, lang="ar"):
        self.lang = lang
        self.engine = PaddleOCR(
            lang=lang,
            enable_mkldnn=False
        )

    def extract_text(self, image_path):
        image_path = validate_image_path(image_path)

        result = self.engine.predict(
            str(image_path)
        )

        parsed_result = parse_paddle_result(result)

        return create_ocr_record(
            file_name=image_path.name,
            source_type="image",
            source_number=1,
            text=parsed_result["text"],
            ocr_engine="PaddleOCR",
            language=self.lang,
            confidence=parsed_result["confidence"]
        )
```

### File: `src/ocr/handwriting_ocr.py`
**Path:** `E:\ZaWolf_project\src\ocr\handwriting_ocr.py`
```python
from pathlib import Path

import torch
from PIL import Image
from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration
)


class HandwritingOCREngine:

    def __init__(self, device="auto"):
        self.device = self._get_device(device)

        self.model_name = (
            "sherif1313/"
            "Arabic-handwritten-OCR-4bit-Qwen2.5-VL-3B-v3"
        )

        self.processor = AutoProcessor.from_pretrained(
            self.model_name
        )

        if self.device == "cuda":
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map="cuda"
            )
        else:
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map="cpu"
            )

        self.model.eval()

    @staticmethod
    def _get_device(device):
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"

        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA requested but no CUDA GPU is available."
            )

        if device not in ["cuda", "cpu"]:
            raise ValueError(
                "Device must be 'auto', 'cuda', or 'cpu'."
            )

        return device

    def extract_text(self, image_path):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Path is not a file: {image_path}"
            )

        image = Image.open(image_path).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe all handwritten text in this image "
                            "exactly as it appears. Preserve medicine names, "
                            "numbers, dosages, units, and instructions. "
                            "Do not add information that is not visible."
                        )
                    }
                ]
            }
        ]

        text_prompt = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text_prompt],
            images=[image],
            return_tensors="pt"
        )

        target_device = torch.device(self.device)

        inputs = {
            key: value.to(target_device)
            if hasattr(value, "to")
            else value
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=512
            )

        input_length = inputs["input_ids"].shape[1]

        generated_text = self.processor.batch_decode(
            generated_ids[:, input_length:],
            skip_special_tokens=True
        )[0].strip()

        return {
            "file_name": image_path.name,
            "source_type": "image",
            "source_number": 1,
            "ocr_engine": "Qwen2.5-VL-3B-Handwriting-OCR",
            "language": "ar/en",
            "text": generated_text,
            "device": self.device,
            "status": "success"
        }
```

### File: `src/ocr/ocr_router.py`
**Path:** `E:\ZaWolf_project\src\ocr\ocr_router.py`
```python
from src.ocr.ocr_engine import OCREngine
from src.ocr.handwriting_ocr import HandwritingOCREngine
from src.ocr.device import get_device


class OCRRouter:

    def __init__(self, device="auto"):
        self.device = get_device(device)
        self.qwen_engine = None
        self.printed_engine = None

    def _get_qwen_engine(self):
        if self.qwen_engine is None:
            self.qwen_engine = HandwritingOCREngine(
                device=self.device
            )

        return self.qwen_engine

    def _get_printed_engine(self):
        if self.printed_engine is None:
            self.printed_engine = OCREngine(lang="ar")

        return self.printed_engine

    def process(self, image_path, engine="qwen"):
        if engine == "qwen":
            return self._get_qwen_engine().extract_text(image_path)

        if engine == "paddle":
            return self._get_printed_engine().extract_text(image_path)

        raise ValueError(
            "Engine must be 'qwen' or 'paddle'."
        )
```

### File: `src/ocr/ocr_utils.py`
**Path:** `E:\ZaWolf_project\src\ocr\ocr_utils.py`
```python
from pathlib import Path


def validate_image_path(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            f"Path is not a file: {image_path}"
        )

    return image_path


def normalize_ocr_text(text):
    if text is None:
        return ""

    return " ".join(str(text).split())


def parse_paddle_result(result):
    texts = []
    scores = []

    for page_result in result:
        data = page_result

        if hasattr(data, "rec_texts"):
            texts.extend(data.rec_texts)
            scores.extend(data.rec_scores)

        elif isinstance(data, dict):
            texts.extend(data.get("rec_texts", []))
            scores.extend(data.get("rec_scores", []))

    clean_texts = [
        normalize_ocr_text(text)
        for text in texts
        if normalize_ocr_text(text)
    ]

    valid_scores = [
        float(score)
        for score in scores
        if score is not None
    ]

    full_text = "\n".join(clean_texts)

    confidence = (
        sum(valid_scores) / len(valid_scores)
        if valid_scores
        else 0.0
    )

    return {
        "text": full_text,
        "confidence": confidence
    }



def create_ocr_record(
    file_name,
    source_type,
    source_number,
    text,
    ocr_engine,
    language="ar",
    confidence=0.0
):
    return {
        "file_name": file_name,
        "source_type": source_type,
        "source_number": source_number,
        "ocr_engine": ocr_engine,
        "language": language,
        "text": normalize_ocr_text(text),
        "confidence": confidence,
        "status": "success"
    }
```

### File: `src/llm/local_llm.py`
**Path:** `E:\ZaWolf_project\src\llm\local_llm.py`
```python
import json
import requests


class LocalLLM:
    def __init__(
        self,
        model="qwen3:latest",
        base_url="http://localhost:11434",
        timeout=600
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt, system_prompt=None):
        print("\n===== LLM DEBUG =====")
        print(f"Model: {self.model}")
        print(f"Prompt length: {len(prompt):,} chars")

        if system_prompt:
            print(f"System prompt length: {len(system_prompt):,} chars")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout
        )

        response.raise_for_status()

        result = response.json()

        if "response" not in result:
            raise ValueError("LLM response field is missing.")

        response_text = result["response"]

        print(f"Response length: {len(response_text):,} chars")
        print("===== END LLM DEBUG =====\n")

        return response_text

    def generate_json(self, prompt, system_prompt=None):
        response_text = self.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as error:
            print("\n===== INVALID JSON RESPONSE =====")
            print(response_text)
            print("===== END INVALID JSON RESPONSE =====\n")

            raise ValueError(
                f"LLM returned invalid JSON: {error}"
            ) from error
```

### File: `src/llm/llm_schema.py`
**Path:** `E:\ZaWolf_project\src\llm\llm_schema.py`
```python
from typing import Optional, List
from pydantic import BaseModel


class LocationData(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class StaffData(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    license_no: Optional[str] = None
    location_name: Optional[str] = None
    is_active: Optional[bool] = None


class ClientData(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    lead_source: Optional[str] = None
    medical_alerts: Optional[str] = None
    opt_in_sms: Optional[bool] = None


class MedicalHistoryData(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: Optional[str] = None


class VitalData(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    weight: Optional[float] = None
    recorded_at: Optional[str] = None


class LabResultData(BaseModel):
    test_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: Optional[str] = None


class MedicationData(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ServiceData(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration_min: Optional[int] = None
    price: Optional[float] = None


class AppointmentData(BaseModel):
    client_name: Optional[str] = None
    staff_name: Optional[str] = None
    location_name: Optional[str] = None
    service_name: Optional[str] = None
    room: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TreatmentRecordData(BaseModel):
    appointment_id: Optional[int] = None
    product_name: Optional[str] = None
    units: Optional[float] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[str] = None
    area: Optional[str] = None
    injection_sites: Optional[str] = None
    depth: Optional[str] = None
    device_settings: Optional[str] = None
    skin_response: Optional[str] = None
    aftercare: Optional[str] = None


class ConsentData(BaseModel):
    appointment_id: Optional[int] = None
    consent_type: Optional[str] = None
    signed_at: Optional[str] = None
    file_ref: Optional[str] = None


class PhotoData(BaseModel):
    treatment_id: Optional[int] = None
    type: Optional[str] = None
    taken_at: Optional[str] = None
    file_ref: Optional[str] = None


class InvoiceData(BaseModel):
    appointment_id: Optional[int] = None
    issue_date: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    status: Optional[str] = None


class InvoiceItemData(BaseModel):
    invoice_id: Optional[int] = None
    item_type: Optional[str] = None
    item_id: Optional[int] = None
    description: Optional[str] = None
    qty: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class PaymentData(BaseModel):
    invoice_id: Optional[int] = None
    amount: Optional[float] = None
    method: Optional[str] = None
    paid_at: Optional[str] = None
    reference: Optional[str] = None


class PackageData(BaseModel):
    name: Optional[str] = None
    sessions_count: Optional[int] = None
    price: Optional[float] = None
    validity_days: Optional[int] = None


class ClientPackageData(BaseModel):
    package_name: Optional[str] = None
    remaining_sessions: Optional[int] = None
    expires_at: Optional[str] = None


class ProductData(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    stock_qty: Optional[float] = None
    cost: Optional[float] = None
    price: Optional[float] = None


class SourceDocumentData(BaseModel):
    file_name: Optional[str] = None
    doc_type: Optional[str] = None
    ocr_text: Optional[str] = None
    llm_json: Optional[dict] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class LLMExtractionResult(BaseModel):
    locations: List[LocationData] = []
    staff: List[StaffData] = []
    clients: List[ClientData] = []
    medical_history: List[MedicalHistoryData] = []
    vitals: List[VitalData] = []
    lab_results: List[LabResultData] = []
    medications: List[MedicationData] = []
    services: List[ServiceData] = []
    appointments: List[AppointmentData] = []
    treatment_records: List[TreatmentRecordData] = []
    consents: List[ConsentData] = []
    photos: List[PhotoData] = []
    invoices: List[InvoiceData] = []
    invoice_items: List[InvoiceItemData] = []
    payments: List[PaymentData] = []
    packages: List[PackageData] = []
    client_packages: List[ClientPackageData] = []
    products: List[ProductData] = []
    source_documents: List[SourceDocumentData] = []
```

### File: `src/llm/llm_processor.py`
**Path:** `E:\ZaWolf_project\src\llm\llm_processor.py`
```python
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
```

### File: `src/validation/extraction_guard.py`
**Path:** `E:\ZaWolf_project\src\validation\extraction_guard.py`
```python
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
```

### File: `src/validation/validator.py`
**Path:** `E:\ZaWolf_project\src\validation\validator.py`
```python
from pydantic import ValidationError

from src.llm.llm_schema import LLMExtractionResult


class DataValidator:
    def validate(self, data):
        try:
            validated = LLMExtractionResult.model_validate(data)

            normalized_data = validated.model_dump()

            return {
                "valid": True,
                "data": normalized_data,
                "errors": []
            }

        except ValidationError as error:
            return {
                "valid": False,
                "data": None,
                "errors": self._format_errors(error)
            }

    def _format_errors(self, error):
        errors = []

        for item in error.errors():
            location = ".".join(str(part) for part in item["loc"])

            errors.append({
                "field": location,
                "message": item["msg"],
                "type": item["type"]
            })

        return errors
```

### File: `src/database/database.py`
**Path:** `E:\ZaWolf_project\src\database\database.py`
```python
import pyodbc


class Database:
    def __init__(self):
        self.connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=localhost;"
            "DATABASE=ZaWolfDB;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )

    def connect(self):
        return pyodbc.connect(self.connection_string)

    def execute(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def insert_and_get_id(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            connection.commit()
            return result[0]
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def fetch_one(self, query, params=None):
        connection = self.connect()

        try:
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            connection.close()

    def test_connection(self):
        result = self.fetch_one("SELECT DB_NAME()")
        return result[0]
```

### File: `src/database/repository.py`
**Path:** `E:\ZaWolf_project\src\database\repository.py`
```python
from src.database.database import Database


class Repository:
    def __init__(self, table_name):
        self.db = Database()
        self.table_name = table_name

    def insert(self, data, cursor=None):
        columns = list(data.keys())
        values = list(data.values())

        column_names = ", ".join(columns)
        placeholders = ", ".join("?" for _ in values)

        query = f"""
        INSERT INTO {self.table_name} ({column_names})
        OUTPUT INSERTED.id
        VALUES ({placeholders})
        """

        if cursor:
            cursor.execute(query, values)
            return cursor.fetchone()[0]

        return self.db.insert_and_get_id(query, values)

    def get_by_id(self, record_id):
        query = f"""
        SELECT *
        FROM {self.table_name}
        WHERE id = ?
        """

        return self.db.fetch_one(query, (record_id,))
```

### File: `src/database/relation_resolver.py`
**Path:** `E:\ZaWolf_project\src\database\relation_resolver.py`
```python
from src.database.database import Database


class RelationResolver:
    def __init__(self):
        self.db = Database()

    def _fetch_one(self, query, params, cursor=None):
        if cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
        else:
            result = self.db.fetch_one(query, params)

        return result[0] if result else None

    def find_client(self, client, cursor=None):
        query = """
        SELECT TOP 1 id
        FROM clients
        WHERE first_name = ?
          AND last_name = ?
          AND (
              mobile = ?
              OR (? IS NULL AND mobile IS NULL)
          )
        """

        params = (
            client.get("first_name"),
            client.get("last_name"),
            client.get("mobile"),
            client.get("mobile"),
        )

        return self._fetch_one(query, params, cursor)

    def find_staff(self, full_name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM staff WHERE full_name = ?",
            (full_name,),
            cursor,
        )

    def find_location(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM locations WHERE name = ?",
            (name,),
            cursor,
        )

    def find_service(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM services WHERE name = ?",
            (name,),
            cursor,
        )

    def find_product(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM products WHERE name = ?",
            (name,),
            cursor,
        )

    def find_package(self, name, cursor=None):
        return self._fetch_one(
            "SELECT TOP 1 id FROM packages WHERE name = ?",
            (name,),
            cursor,
        )
```

### File: `src/database/mapper.py`
**Path:** `E:\ZaWolf_project\src\database\mapper.py`
```python
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
```

### File: `src/database/appointment_repository.py`
**Path:** `E:\ZaWolf_project\src\database\appointment_repository.py`
```python
from src.database.database import Database


class AppointmentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        staff_id,
        location_id,
        service_id,
        room=None,
        start_at=None,
        end_at=None,
        status=None,
        notes=None,
    ):
        query = """
        INSERT INTO appointments (
            client_id,
            staff_id,
            location_id,
            service_id,
            room,
            start_at,
            end_at,
            status,
            notes
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            staff_id,
            location_id,
            service_id,
            room,
            start_at,
            end_at,
            status,
            notes,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/client_package_repository.py`
**Path:** `E:\ZaWolf_project\src\database\client_package_repository.py`
```python
from src.database.database import Database


class ClientPackageRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        package_id,
        remaining_sessions=None,
        expires_at=None,
    ):
        query = """
        INSERT INTO client_packages (
            client_id,
            package_id,
            remaining_sessions,
            expires_at
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
        """

        params = (
            client_id,
            package_id,
            remaining_sessions,
            expires_at,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/client_repository.py`
**Path:** `E:\ZaWolf_project\src\database\client_repository.py`
```python
from src.database.database import Database


class ClientRepository:
    def __init__(self):
        self.db = Database()

    def create(self, client):
        query = """
        INSERT INTO clients (
            first_name,
            last_name,
            dob,
            gender,
            mobile,
            email,
            address,
            lead_source,
            medical_alerts,
            opt_in_sms
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client.get("first_name"),
            client.get("last_name"),
            client.get("dob"),
            client.get("gender"),
            client.get("mobile"),
            client.get("email"),
            client.get("address"),
            client.get("lead_source"),
            client.get("medical_alerts"),
            client.get("opt_in_sms"),
        )

        result = self.db.fetch_one(query, params)
        return result[0]
```

### File: `src/database/consent_repository.py`
**Path:** `E:\ZaWolf_project\src\database\consent_repository.py`
```python
from src.database.database import Database


class ConsentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        appointment_id=None,
        consent_type=None,
        signed_at=None,
        file_ref=None,
    ):
        query = """
        INSERT INTO consents (
            client_id,
            appointment_id,
            consent_type,
            signed_at,
            file_ref
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            appointment_id,
            consent_type,
            signed_at,
            file_ref,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/invoice_item_repository.py`
**Path:** `E:\ZaWolf_project\src\database\invoice_item_repository.py`
```python
from src.database.database import Database


class InvoiceItemRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        invoice_id,
        item_type=None,
        item_id=None,
        description=None,
        qty=None,
        unit_price=None,
        line_total=None,
    ):
        query = """
        INSERT INTO invoice_items (
            invoice_id,
            item_type,
            item_id,
            description,
            qty,
            unit_price,
            line_total
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            invoice_id,
            item_type,
            item_id,
            description,
            qty,
            unit_price,
            line_total,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/invoice_repository.py`
**Path:** `E:\ZaWolf_project\src\database\invoice_repository.py`
```python
from src.database.database import Database


class InvoiceRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        appointment_id=None,
        issue_date=None,
        subtotal=None,
        discount=None,
        tax=None,
        total=None,
        status=None,
    ):
        query = """
        INSERT INTO invoices (
            client_id,
            appointment_id,
            issue_date,
            subtotal,
            discount,
            tax,
            total,
            status
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            appointment_id,
            issue_date,
            subtotal,
            discount,
            tax,
            total,
            status,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/package_repository.py`
**Path:** `E:\ZaWolf_project\src\database\package_repository.py`
```python
from src.database.database import Database


class PackageRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        name,
        sessions_count=None,
        price=None,
        validity_days=None,
    ):
        query = """
        INSERT INTO packages (
            name,
            sessions_count,
            price,
            validity_days
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?)
        """

        params = (
            name,
            sessions_count,
            price,
            validity_days,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/payment_repository.py`
**Path:** `E:\ZaWolf_project\src\database\payment_repository.py`
```python
from src.database.database import Database


class PaymentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        invoice_id,
        amount,
        method=None,
        paid_at=None,
        reference=None,
    ):
        query = """
        INSERT INTO payments (
            invoice_id,
            amount,
            method,
            paid_at,
            reference
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            invoice_id,
            amount,
            method,
            paid_at,
            reference,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/photo_repository.py`
**Path:** `E:\ZaWolf_project\src\database\photo_repository.py`
```python
from src.database.database import Database


class PhotoRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        client_id,
        treatment_id=None,
        photo_type=None,
        taken_at=None,
        file_ref=None,
    ):
        query = """
        INSERT INTO photos (
            client_id,
            treatment_id,
            type,
            taken_at,
            file_ref
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            client_id,
            treatment_id,
            photo_type,
            taken_at,
            file_ref,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/database/source_document_repository.py`
**Path:** `E:\ZaWolf_project\src\database\source_document_repository.py`
```python
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
```

### File: `src/database/treatment_repository.py`
**Path:** `E:\ZaWolf_project\src\database\treatment_repository.py`
```python
from src.database.database import Database


class TreatmentRepository:
    def __init__(self):
        self.db = Database()

    def create(
        self,
        appointment_id,
        product_id,
        units=None,
        lot_number=None,
        expiry_date=None,
        area=None,
        injection_sites=None,
        depth=None,
        device_settings=None,
        skin_response=None,
        aftercare=None,
    ):
        query = """
        INSERT INTO treatment_records (
            appointment_id,
            product_id,
            units,
            lot_number,
            expiry_date,
            area,
            injection_sites,
            depth,
            device_settings,
            skin_response,
            aftercare
        )
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            appointment_id,
            product_id,
            units,
            lot_number,
            expiry_date,
            area,
            injection_sites,
            depth,
            device_settings,
            skin_response,
            aftercare,
        )

        return self.db.insert_and_get_id(query, params)
```

### File: `src/utils.py`
**Path:** `E:\ZaWolf_project\src\utils.py`
```python
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
```

### File: `src/pipeline.py`
**Path:** `E:\ZaWolf_project\src\pipeline.py`
```python
from pathlib import Path
import json

import pandas as pd

from src.ingestion.file_detector import detect_file_type
from src.ingestion.router import route_file

from src.processors.pdf_processor import (
    detect_pdf_type,
    process_pdf_to_chunks,
    convert_pdf_to_images,
)

from src.processors.word_processor import process_word
from src.processors.structured_processor import extract_structured_data
from src.processors.image_processor import process_image

from src.ocr.ocr_router import OCRRouter

from src.llm.llm_processor import LLMProcessor
from src.validation.validator import DataValidator
from src.database.mapper import DatabaseMapper

from config.settings import PROCESSED_DIR


class ProcessingPipeline:

    def __init__(self, ocr_engine="qwen"):
        self.llm_processor = LLMProcessor()
        self.validator = DataValidator()
        self.database_mapper = DatabaseMapper()

        self.ocr_router = OCRRouter()
        self.ocr_engine = ocr_engine

    def process_file(self, file_path):

        try:
            file_info = detect_file_type(file_path)

            if not file_info["supported"]:
                return {
                    "status": "unsupported",
                    "data": None,
                    "source_text": "",
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "unsupported_file",
                            "message": (
                                f"Unsupported file type: "
                                f"{file_info.get('extension')}"
                            ),
                        }
                    ],
                }

            route = route_file(file_info)

            if route == "pdf_pipeline":
                return self._process_pdf_file(file_info)

            if route in [
                "excel_pipeline",
                "csv_pipeline",
            ]:
                return self._process_structured_file(
                    file_info
                )

            text = self._extract_text(
                file_info,
                route,
            )

            if not text.strip():
                return {
                    "status": "invalid",
                    "data": None,
                    "source_text": "",
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "empty_text",
                            "message": (
                                "No text extracted from file."
                            ),
                        }
                    ],
                }

            result = self.process_text(text)

            if result["status"] == "valid":
                result["source_text"] = text

                if route == "image_pipeline":
                    result["ocr_text"] = text
                else:
                    result["ocr_text"] = ""

                result["source_metadata"] = {
                    "file_name": Path(
                        file_info["file_path"]
                    ).name,
                    "route": route,
                    "ocr_engine": (
                        self.ocr_engine
                        if route == "image_pipeline"
                        else None
                    ),
                }

            return result

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": "pipeline_error",
                        "message": str(error),
                    }
                ],
            }

    def process_and_save_file(self, file_path):

        result = self.process_file(
            file_path
        )

        if result["status"] != "valid":
            return result

        if result.get("structured_data") is not None:

            return {
                "status": "valid",
                "data": result.get("data"),
                "structured_data": result.get(
                    "structured_data"
                ),
                "structured_summary": result.get(
                    "structured_summary"
                ),
                "inserted": {},
                "errors": [],
            }

        try:

            data = result["data"]

            source_metadata = result.get(
                "source_metadata",
                {},
            )

            source_text = result.get(
                "source_text",
                "",
            )

            ocr_text = result.get(
                "ocr_text",
                "",
            )

            source_document = (
                self._build_source_document(
                    file_path=file_path,
                    data=data,
                    source_metadata=source_metadata,
                    source_text=source_text,
                    ocr_text=ocr_text,
                )
            )

            if source_document:

                data = data.copy()

                source_documents = list(
                    data.get(
                        "source_documents",
                        [],
                    )
                )

                source_documents.append(
                    source_document
                )

                data["source_documents"] = (
                    source_documents
                )

            inserted = self.database_mapper.save(
                data
            )

            return {
                "status": "saved",
                "data": data,
                "inserted": inserted,
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": result.get("data"),
                "inserted": {},
                "errors": [
                    {
                        "type": "database_error",
                        "message": str(error),
                    }
                ],
            }

    def process_text(self, text):

        try:

            llm_data = self.llm_processor.process(
                text
            )

            validation_result = (
                self.validator.validate(
                    llm_data
                )
            )

            if not validation_result["valid"]:

                return {
                    "status": "invalid",
                    "data": validation_result.get(
                        "data"
                    ),
                    "source_text": text,
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": (
                        validation_result.get(
                            "errors",
                            [],
                        )
                    ),
                }

            return {
                "status": "valid",
                "data": validation_result["data"],
                "source_text": text,
                "ocr_text": "",
                "source_metadata": {},
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "source_text": text,
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": "text_processing_error",
                        "message": str(error),
                    }
                ],
            }

    def process_and_save(self, text):

        result = self.process_text(
            text
        )

        if result["status"] != "valid":
            return result

        try:

            data = result["data"]

            inserted = self.database_mapper.save(
                data
            )

            return {
                "status": "saved",
                "data": data,
                "inserted": inserted,
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": result["data"],
                "inserted": {},
                "errors": [
                    {
                        "type": "database_error",
                        "message": str(error),
                    }
                ],
            }

    def _extract_text(
        self,
        file_info,
        route,
    ):

        file_path = Path(
            file_info["file_path"]
        )

        if route == "word_pipeline":
            return self._process_word(
                file_path
            )

        if route in [
            "excel_pipeline",
            "csv_pipeline",
        ]:
            raise ValueError(
                "Structured files must be processed "
                "through _process_structured_file()."
            )

        if route == "image_pipeline":
            return self._process_image(
                file_path
            )

        raise ValueError(
            f"Unsupported route: {route}"
        )

    def _process_word(
        self,
        file_path,
    ):

        result = process_word(
            file_path
        )

        text_parts = []

        for batch in result:

            if not isinstance(
                batch,
                list,
            ):
                continue

            for chunk in batch:

                if not isinstance(
                    chunk,
                    dict,
                ):
                    continue

                text = chunk.get(
                    "text"
                )

                if text:
                    text_parts.append(
                        text
                    )

        return "\n\n".join(
            text_parts
        )

    def _process_structured_file(
        self,
        file_info,
    ):

        try:

            structured_data = (
                extract_structured_data(
                    file_info
                )
            )

            if not structured_data:

                return {
                    "status": "invalid",
                    "data": None,
                    "structured_data": None,
                    "structured_summary": None,
                    "errors": [
                        {
                            "type": (
                                "empty_structured_data"
                            ),
                            "message": (
                                "No structured data "
                                "extracted."
                            ),
                        }
                    ],
                }

            sheets = structured_data.get(
                "sheets",
                {},
            )

            if not sheets:

                return {
                    "status": "invalid",
                    "data": None,
                    "structured_data": (
                        structured_data
                    ),
                    "structured_summary": None,
                    "errors": [
                        {
                            "type": "empty_sheets",
                            "message": (
                                "No sheets found "
                                "in structured file."
                            ),
                        }
                    ],
                }

            sheet_summary = {}

            for (
                sheet_name,
                dataframe,
            ) in sheets.items():

                if not isinstance(
                    dataframe,
                    pd.DataFrame,
                ):

                    return {
                        "status": "invalid",
                        "data": None,
                        "structured_data": (
                            structured_data
                        ),
                        "structured_summary": None,
                        "errors": [
                            {
                                "type": (
                                    "invalid_sheet_data"
                                ),
                                "message": (
                                    f"Sheet '{sheet_name}' "
                                    "does not contain a "
                                    "pandas DataFrame."
                                ),
                            }
                        ],
                    }

                sheet_summary[
                    sheet_name
                ] = {
                    "rows": len(
                        dataframe
                    ),
                    "columns": len(
                        dataframe.columns
                    ),
                    "column_names": (
                        dataframe.columns.tolist()
                    ),
                }

            return {
                "status": "valid",
                "data": self._create_empty_data(),
                "structured_data": (
                    structured_data
                ),
                "structured_summary": (
                    sheet_summary
                ),
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {
                    "file_name": Path(
                        file_info["file_path"]
                    ).name,
                    "route": "structured",
                    "ocr_engine": None,
                },
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "structured_data": None,
                "structured_summary": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "structured_processing_error"
                        ),
                        "message": str(error),
                    }
                ],
            }

    def _process_image(
        self,
        file_path,
    ):

        processed_image = process_image(
            file_path
        )

        if isinstance(
            processed_image,
            dict,
        ):

            image_path = (
                processed_image.get(
                    "processed_path"
                )
            )

            if image_path:

                ocr_result = (
                    self.ocr_router.process(
                        image_path,
                        engine=self.ocr_engine,
                    )
                )

            else:

                ocr_result = (
                    self.ocr_router.process(
                        file_path,
                        engine=self.ocr_engine,
                    )
                )

        else:

            ocr_result = (
                self.ocr_router.process(
                    processed_image,
                    engine=self.ocr_engine,
                )
            )

        if not ocr_result.get("text"):
            return ""

        return ocr_result["text"]

    def _process_pdf_file(
        self,
        file_info,
    ):

        file_path = Path(
            file_info["file_path"]
        )

        pdf_info = detect_pdf_type(
            file_path
        )

        if pdf_info["pdf_type"] == "digital":

            return self._process_digital_pdf(
                file_path
            )

        return self._process_scanned_pdf(
            file_path
        )

    def _process_digital_pdf(
        self,
        file_path,
    ):

        merged_data = (
            self._create_empty_data()
        )

        batch_count = 0
        text_parts = []

        for batch_chunks in process_pdf_to_chunks(
            file_path
        ):

            batch_text = "\n\n".join(
                chunk["text"]
                for chunk in batch_chunks
                if chunk.get("text")
            )

            if not batch_text.strip():
                continue

            batch_count += 1

            text_parts.append(
                batch_text
            )

            batch_result = self.process_text(
                batch_text
            )

            if batch_result["status"] != "valid":

                return {
                    "status": (
                        batch_result["status"]
                    ),
                    "data": None,
                    "source_text": (
                        "\n\n".join(
                            text_parts
                        )
                    ),
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "pdf_batch_error",
                            "batch": batch_count,
                            "errors": (
                                batch_result[
                                    "errors"
                                ]
                            ),
                        }
                    ],
                }

            merged_data = (
                self._merge_extracted_data(
                    merged_data,
                    batch_result["data"],
                )
            )

        if batch_count == 0:

            return {
                "status": "invalid",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "empty_digital_pdf"
                        ),
                        "message": (
                            "No text batches were "
                            "extracted from the "
                            "digital PDF."
                        ),
                    }
                ],
            }

        validation_result = (
            self.validator.validate(
                merged_data
            )
        )

        if not validation_result["valid"]:

            return {
                "status": "invalid",
                "data": validation_result.get(
                    "data"
                ),
                "source_text": (
                    "\n\n".join(
                        text_parts
                    )
                ),
                "ocr_text": "",
                "source_metadata": {},
                "errors": (
                    validation_result.get(
                        "errors",
                        [],
                    )
                ),
            }

        return {
            "status": "valid",
            "data": validation_result["data"],
            "source_text": (
                "\n\n".join(
                    text_parts
                )
            ),
            "ocr_text": "",
            "source_metadata": {
                "file_name": file_path.name,
                "route": "digital_pdf",
                "ocr_engine": None,
            },
            "errors": [],
        }

    def _process_scanned_pdf(
        self,
        file_path,
    ):

        output_dir = (
            Path(PROCESSED_DIR)
            / "pdf_images"
        )

        text_parts = []
        confidence_values = []

        for page in convert_pdf_to_images(
            file_path,
            output_dir,
        ):

            ocr_result = (
                self.ocr_router.process(
                    page["image_path"],
                    engine=self.ocr_engine,
                )
            )

            page_text = ocr_result.get(
                "text",
                "",
            )

            if page_text:
                text_parts.append(
                    page_text
                )

            confidence = ocr_result.get(
                "confidence"
            )

            if isinstance(
                confidence,
                (int, float),
            ):
                confidence_values.append(
                    float(confidence)
                )

        text = "\n\n".join(
            text_parts
        )

        if not text.strip():

            return {
                "status": "invalid",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "empty_scanned_pdf"
                        ),
                        "message": (
                            "No text extracted "
                            "from scanned PDF."
                        ),
                    }
                ],
            }

        result = self.process_text(
            text
        )

        if result["status"] != "valid":
            return result

        average_confidence = None

        if confidence_values:

            average_confidence = (
                sum(confidence_values)
                / len(confidence_values)
            )

        result["source_text"] = text
        result["ocr_text"] = text

        result["source_metadata"] = {
            "file_name": file_path.name,
            "route": "scanned_pdf",
            "ocr_engine": self.ocr_engine,
            "ocr_confidence": (
                average_confidence
            ),
        }

        return result

    def _build_source_document(
        self,
        file_path,
        data,
        source_metadata,
        source_text,
        ocr_text,
    ):

        file_path = Path(
            file_path
        )

        route = source_metadata.get(
            "route",
            "",
        )

        if route == "structured":
            return None

        if route == "image_pipeline":

            doc_type = "image"

        elif route == "digital_pdf":

            doc_type = "digital_pdf"

        elif route == "scanned_pdf":

            doc_type = "scanned_pdf"

        elif route == "word_pipeline":

            doc_type = "word"

        else:

            doc_type = (
                route
                or file_path.suffix.lower()
            )

        return {
            "file_name": file_path.name,
            "doc_type": doc_type,
            "ocr_text": (
                ocr_text
                if ocr_text
                else None
            ),
            "llm_json": json.dumps(
                data,
                ensure_ascii=False,
                default=str,
            ),
            "review_status": "auto_processed",
        }

    def _create_empty_data(self):

        return {
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
            "source_documents": [],
        }

    def _merge_extracted_data(
        self,
        merged_data,
        batch_data,
    ):

        for table in merged_data:

            records = batch_data.get(
                table,
                [],
            )

            if not isinstance(
                records,
                list,
            ):
                continue

            merged_data[
                table
            ].extend(records)

        return merged_data
```

### File: `main.py`
**Path:** `E:\ZaWolf_project\main.py`
```python
from src.pipeline import run_pipeline


if __name__ == "__main__":
    results = run_pipeline()

    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)

    for index, result in enumerate(results, start=1):
        file_info = result.get("file", {})

        print(
            f"{index}. "
            f"{file_info.get('name')} | "
            f"{file_info.get('type')} | "
            f"{result.get('content_type')}"
        )

    print("\n" + "=" * 80)
    print(f"Pipeline completed: {len(results)} files processed.")
    print("=" * 80)
```

### File: `tests/test_full_system_e2e.py`
**Path:** `E:\ZaWolf_project\tests\test_full_system_e2e.py`
```python
from pathlib import Path

from src.pipeline import ProcessingPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEST_FILES = {
    "digital_pdf": PROJECT_ROOT / "data" / "processed" / "digital_pdf_test_5_pages.pdf",
    "scanned_pdf": PROJECT_ROOT / "data" / "processed" / "scanned_pdf_test_3_pages.pdf",
    "word": PROJECT_ROOT / "data" / "input" / "MediVerse_Doc.docx",
    "csv": PROJECT_ROOT / "data" / "input" / "Covid-19 Dataset .csv",
    "excel": PROJECT_ROOT / "data" / "processed" / "excel_test.xlsx",
    "image": PROJECT_ROOT / "data" / "input" / "english_real.png",
    "handwritten_image": PROJECT_ROOT / "data" / "input" / "hand_write.jpg",
}


def main():
    pipeline = ProcessingPipeline(ocr_engine="qwen")

    results = {}

    print("=" * 100)
    print("FINAL FULL SYSTEM E2E TEST")
    print("=" * 100)

    for input_type, file_path in TEST_FILES.items():
        print("\n" + "=" * 100)
        print(f"TEST: {input_type}")
        print(f"FILE: {file_path}")
        print("=" * 100)

        if not file_path.exists():
            results[input_type] = {
                "status": "missing",
                "inserted": {},
                "errors": [f"File not found: {file_path}"],
            }

            print("STATUS: MISSING")
            continue

        try:
            result = pipeline.process_and_save_file(file_path)

            status = result.get("status")
            inserted = result.get("inserted", {})
            errors = result.get("errors", [])

            results[input_type] = {
                "status": status,
                "inserted": inserted,
                "errors": errors,
            }

            print("STATUS:", status)
            print("ERRORS:", errors)
            print("INSERTED:", inserted)

            if result.get("data") is not None:
                data = result["data"]

                data_counts = {
                    key: len(value)
                    for key, value in data.items()
                    if isinstance(value, list)
                }

                print("DATA COUNTS:", data_counts)

            if result.get("structured_summary") is not None:
                print(
                    "STRUCTURED SUMMARY:",
                    result["structured_summary"],
                )

        except Exception as error:
            results[input_type] = {
                "status": "error",
                "inserted": {},
                "errors": [str(error)],
            }

            print("STATUS: ERROR")
            print("ERROR:", error)

    print("\n")
    print("=" * 100)
    print("FINAL TEST REPORT")
    print("=" * 100)

    passed = 0
    failed = 0

    for input_type, result in results.items():
        status = result["status"]

        if status in {"saved", "valid"}:
            print(f"[PASS] {input_type} -> {status}")
            passed += 1
        else:
            print(f"[FAIL] {input_type} -> {status}")
            print("       Errors:", result["errors"])
            failed += 1

    print("=" * 100)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"TOTAL:  {len(results)}")
    print("=" * 100)

    if failed == 0:
        print("FINAL FULL SYSTEM TEST: PASS")
    else:
        print("FINAL FULL SYSTEM TEST: FAIL")


if __name__ == "__main__":
    main()
```

### File: `tests/run_real_integration_test.py`
**Path:** `E:\ZaWolf_project\tests\run_real_integration_test.py`
```python
import csv
import time
from pathlib import Path

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from src.pipeline import ProcessingPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_TEST_DIR = PROJECT_ROOT / "real_test"
RESULTS_DIR = REAL_TEST_DIR / "results"
RESULTS_FILE = RESULTS_DIR / "real_integration_test.csv"


def first_files(folder, extensions, count):
    files = []

    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            files.append(path)

    return files[:count]


def build_test_files():
    files = []

    files.extend(
        first_files(
            REAL_TEST_DIR / "handwritten",
            {".jpg", ".jpeg", ".png"},
            2,
        )
    )

    files.extend(
        first_files(
            REAL_TEST_DIR / "images",
            {".jpg", ".jpeg", ".png"},
            2,
        )
    )

    files.extend(
        first_files(
            REAL_TEST_DIR / "csv",
            {".csv"},
            1,
        )
    )

    files.extend(
        first_files(
            REAL_TEST_DIR / "docx",
            {".docx"},
            1,
        )
    )

    files.extend(
        first_files(
            REAL_TEST_DIR / "pdf",
            {".pdf"},
            2,
        )
    )

    return files


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    test_files = build_test_files()
    total = len(test_files)

    print("=" * 70)
    print("ZaWolf REAL DATA + DATABASE INTEGRATION TEST")
    print("=" * 70)
    print(f"Total files: {total}")
    print(f"Results: {RESULTS_FILE}")
    print("=" * 70)

    pipeline = ProcessingPipeline(ocr_engine="qwen")

    success = 0
    errors = 0

    with RESULTS_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "index",
                "total",
                "file_name",
                "file_type",
                "status",
                "processing_seconds",
                "inserted",
                "error",
            ],
        )

        writer.writeheader()

        for index, file_path in enumerate(
            test_files,
            start=1,
        ):
            print()
            print("=" * 70)
            print(
                f"[{index}/{total}] "
                f"{file_path.suffix.upper()} "
                f"{file_path.name}"
            )
            print("=" * 70)

            start_time = time.perf_counter()

            try:
                result = pipeline.process_and_save_file(
                    file_path
                )

                elapsed = time.perf_counter() - start_time

                status = result.get(
                    "status",
                    "unknown",
                )

                inserted = result.get(
                    "inserted",
                    {},
                )

                errors_list = result.get(
                    "errors",
                    [],
                )

                error_message = str(errors_list)

                if status == "saved":
                    success += 1
                else:
                    errors += 1

                print(
                    f"Status: {status}"
                )

                print(
                    f"Time: {elapsed:.2f}s"
                )

                print(
                    f"Inserted: {inserted}"
                )

                if errors_list:
                    print(
                        f"Errors: {errors_list}"
                    )

                writer.writerow({
                    "index": index,
                    "total": total,
                    "file_name": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "status": status,
                    "processing_seconds": round(
                        elapsed,
                        2,
                    ),
                    "inserted": str(inserted),
                    "error": error_message,
                })

                csv_file.flush()

            except Exception as error:
                elapsed = time.perf_counter() - start_time
                errors += 1

                print(
                    "Status: exception"
                )

                print(
                    f"Time: {elapsed:.2f}s"
                )

                print(
                    f"Error: {error}"
                )

                writer.writerow({
                    "index": index,
                    "total": total,
                    "file_name": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "status": "exception",
                    "processing_seconds": round(
                        elapsed,
                        2,
                    ),
                    "inserted": "{}",
                    "error": str(error),
                })

                csv_file.flush()

    print()
    print("=" * 70)
    print("INTEGRATION TEST FINISHED")
    print("=" * 70)
    print(f"Total: {total}")
    print(f"Saved successfully: {success}")
    print(f"Errors: {errors}")
    print(f"Results: {RESULTS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
```
