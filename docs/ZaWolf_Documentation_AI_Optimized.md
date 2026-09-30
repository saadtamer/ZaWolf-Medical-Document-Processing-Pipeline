# SYSTEM CONTEXT SPECIFICATION: ZaWolf Medical Document Processing & OCR Architecture
# INGESTION DIRECTIVE: READ-AND-RETAIN IN WORKING MEMORY. THIS FILE IS THE CANONICAL ARCHITECTURAL TRUTH.

```yaml
system_identity:
  name: ZaWolf_project
  type: Enterprise Medical Document Processing, OCR, and Entity Extraction Pipeline
  deployment_model: Local / On-Premise Only (Air-gapped compatible, Zero External Cloud API Dependency)
  runtime_environment:
    os: Windows
    python_version: 3.11.9
    dbms: Microsoft SQL Server (Local, Windows Auth / Trusted_Connection)
    llm_runtime: Ollama Local Server (http://localhost:11434, default model: qwen3:latest)
    vision_ocr_backend: PyTorch (CUDA if available, fallback CPU) + Transformers
  project_root: "E:\\ZaWolf_project"
  timestamp_updated: "2026-09-30"
```

---

## 1. CORE SYSTEM INVARIANTS (IMMUTABLE ARCHITECTURAL RULES)

An AI assistant modifying, extending, or reasoning about this codebase MUST NEVER violate these invariants:

1. **Strict Deterministic Ingestion:** File type identification is strictly rule-based via file extensions (`src/ingestion/file_detector.py`) and routed deterministically (`src/ingestion/router.py`). No heuristic guesses or speculative routing.
2. **Unified Image/OCR Branch:** Scanned PDF documents NEVER possess a separate OCR engine. Scanned PDF pages are converted directly to PNG raster images (`src/processors/pdf_processor.py`) and enter the EXACT SAME Image/OCR pipeline as standard standalone images.
3. **No OCR for Native Structured & Word Documents:** Word (`.docx`), Excel (`.xlsx`, `.xls`), and CSV (`.csv`) NEVER pass through OCR. Word is parsed via AST/DOM paragraphs and tables; tabular files are parsed directly via Pandas DataFrames.
4. **Extraction-Only Upstream:** Raw file processors NEVER perform data quality filtering, entity deduplication, or missing value imputation. Missing data is preserved as `null`/`None`.
5. **Zero Hallucination / Zero Synthetic IDs in LLM Layer:** The Local LLM (`src/llm/llm_processor.py`) is solely an unstructured-to-structured normalization and mapping engine. It MUST NOT create database primary keys, infer unstated relationships, or generate hallucinated medical details.
6. **Prescription Entity Isolation (Guardrail):** If an input is identified as a medical prescription (via Arabic/English prescription markers in `src/validation/extraction_guard.py`), all non-medication clinical tables (appointments, invoices, lab results, etc.) are atomically wiped to prevent cross-table hallucination leakage.
7. **Atomic Single-Transaction Database Persistence:** Every processed document that is persisted to SQL Server (`src/database/mapper.py`) is committed using a SINGLE transaction and a SINGLE database cursor across all 19 relational tables. If any insert or foreign key resolution fails, `connection.rollback()` is immediately invoked.
8. **Relational Resolution Precedence:** Primary Keys and Foreign Keys are resolved at the database layer via `src/database/relation_resolver.py` (lookup by composite unique identifiers like `(first_name, last_name, mobile)` for clients).

---

## 2. SYSTEM ARCHITECTURE & DATA FLOW GRAPH

```
[Inbound File Path]
       │
       ▼
[src/ingestion/file_detector.py :: detect_file_type()]
       │
       ▼
[src/ingestion/router.py :: route_file()]
       ├─────────────────┬────────────────────┬─────────────────┬─────────────────┐
       │ (pdf)           │ (image)            │ (word)          │ (excel / csv)   │
       ▼                 ▼                    ▼                 ▼                 │
[pdf_pipeline]    [image_pipeline]     [word_pipeline]   [excel/csv_pipeline]     │ (unsupported)
       │                 │                    │                 │                 ▼
       ├─ Digital        │                    │                 │             [Return
       │   │             │                    │                 │             status:
       │   ▼             │                    │                 │           unsupported]
       │ [fitz extract]  │                    │                 │
       │   │             │                    │                 │
       │   ▼             │                    │                 │
       │ [Batch Chunks]  │                    │                 │
       │                 │                    │                 │
       └─ Scanned        │                    │                 │
           │             │                    │                 │
           ▼             │                    │                 │
     [fitz render]       │                    │                 │
     (pages -> images)   │                    │                 │
           │             │                    │                 │
           └──────┬──────┘                    │                 │
                  │                           │                 │
                  ▼                           │                 │
     [src/processors/image_processor.py]      │                 │
     (EXIF transpose, Grayscale, Contrast)    │                 │
                  │                           │                 │
                  ▼                           │                 │
     [src/ocr/ocr_router.py :: OCRRouter]     │                 │
     ├── engine="paddle" -> OCREngine         │                 │
     └── engine="qwen"   -> HandwritingOCREngine                │
                  │                           │                 │
                  ▼                           │                 │
         [Extracted OCR Text]                 │                 │
                  │                           │                 │
                  └─────────────┬─────────────┘                 │
                                │                               │
                                ▼                               ▼
                  [src/processors/word_processor.py]  [src/processors/structured_processor.py]
                  (paragraphs & tables batching)      (pandas DataFrames per sheet)
                                │                               │
                                ▼                               ▼
                  [Unified Extracted Text String]     [Return Structured Summary & Data]
                                │
                                ▼
                  [src/llm/llm_processor.py :: LLMProcessor]
                  ├── LocalLLM via Ollama (format: json, stream: false)
                  ├── Medical Prompt Matrix (Strict block rules, zero-invent)
                  ├── Numeric & Date Normalization (%Y-%m-%d, %Y-%m-%d %H:%M:%S)
                  └── ExtractionGuard (Prescription isolation & empty entity removal)
                                │
                                ▼
                  [src/validation/validator.py :: DataValidator]
                  └── Pydantic Validation via LLMExtractionResult
                                │
                                ├─ Invalid ──► [Return status: invalid + errors]
                                │
                                ▼ (Valid)
                  [src/database/mapper.py :: DatabaseMapper.save()]
                  ├── Single Transaction (connection.cursor())
                  ├── Sequential Insert Order (19 Relational Tables)
                  ├── Foreign Key Resolution (src/database/relation_resolver.py)
                  └── Atomic Commit / Automatic Rollback on Failure
                                │
                                ▼
                  [Return status: saved + inserted IDs dict]
```

---

## 3. COMPLETE CODEBASE SYMBOL & MODULE INDEX

### 3.1 `config/`
* **`config/settings.py`**:
  * `PROJECT_ROOT: Path` = `E:\ZaWolf_project`
  * `DATA_DIR: Path` = `PROJECT_ROOT / "data"`
  * `INPUT_DIR: Path` = `DATA_DIR / "input"`
  * `PROCESSED_DIR: Path` = `DATA_DIR / "processed"`
  * `OUTPUT_DIR: Path` = `DATA_DIR / "output"`
  * `IMAGE_PROCESSED_DIR: Path` = `PROCESSED_DIR / "images"`
  * `PDF_IMAGES_DIR: Path` = `PROCESSED_DIR / "pdf_images"`
  * `MODELS_DIR: Path` = `PROJECT_ROOT / "models"`
  * `LOGS_DIR: Path` = `PROJECT_ROOT / "logs"`
  * `MAX_BATCH_TEXT_SIZE: int = 12000` (Characters)
  * `BATCH_MEMORY_SAFETY_RATIO: float = 0.25`
  * `SUPPORTED_IMAGE_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".webp"]`
  * `SUPPORTED_EXTENSIONS: dict[str, str] = {".pdf": "pdf", ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image", ".xlsx": "excel", ".xls": "excel", ".csv": "csv", ".docx": "word"}`

### 3.2 `src/utils.py`
* `text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300, separators=["\n\n", "\n", ". ", " ", ""])`
* `get_dynamic_batch_limit() -> dict`:
  * Returns: `{"available_bytes": int, "memory_budget_bytes": int}`.
  * Calculates budget as `psutil.virtual_memory().available * BATCH_MEMORY_SAFETY_RATIO`.
* `batch_text_units(text_units: list[dict]) -> Generator[list[dict]]`:
  * Batches text units while respecting both character length limit (`MAX_BATCH_TEXT_SIZE`) and byte memory budget.
* `create_text_chunks(text_batch: list[dict], file_name: str) -> list[dict]`:
  * Returns chunks with keys: `file_name`, `chunk_index`, `text`, `text_length`.
* `process_text_units(text_units: list[dict], file_name: str) -> Generator[list[dict]]`:
  * Pipeline helper chaining `batch_text_units` and `create_text_chunks`.
* `create_content_record(file_name, file_type, content, source_type=None, source_number=None) -> dict`.

### 3.3 `src/ingestion/`
* **`src/ingestion/file_detector.py`**:
  * `get_input_files() -> list[Path]`: Lists all files in `INPUT_DIR`.
  * `detect_file_type(file_path: Union[str, Path]) -> dict`:
    * Throws: `FileNotFoundError` if path does not exist.
    * Returns:
      ```python
      {
          "file_name": str,
          "file_path": str,
          "extension": str,       # lowercased, e.g. ".pdf"
          "file_type": str,       # "pdf" | "image" | "excel" | "csv" | "word" | "unsupported"
          "supported": bool
      }
      ```
* **`src/ingestion/router.py`**:
  * `route_file(file_info: dict) -> str`:
    * Mapping: `pdf -> "pdf_pipeline"`, `image -> "image_pipeline"`, `excel -> "excel_pipeline"`, `csv -> "csv_pipeline"`, `word -> "word_pipeline"`, default `-> "unsupported"`.

### 3.4 `src/processors/`
* **`src/processors/pdf_processor.py`**:
  * `detect_pdf_type(file_path: Path) -> dict`:
    * Evaluates cumulative text length extracted across all pages via `page.get_text("text").strip()`.
    * If `text_length > 0` returns `"digital"`, else returns `"scanned"`.
  * `extract_pdf_pages(file_path: Path) -> Generator[list[dict]]`:
    * Yields memory-aware batches of extracted text pages.
  * `process_pdf_to_chunks(file_path: Path) -> Generator[list[dict]]`:
    * High-level generator yielding contextual chunks using `create_contextual_chunks`.
  * `convert_pdf_to_images(file_path: Path, output_dir: Path) -> Generator[dict]`:
    * Renders each page via `fitz.Matrix(1, 1)` into a PNG file: `{stem}_page_{page_number}.png`.
    * Yields: `{"file_name": str, "page_number": int, "image_path": str}`.
* **`src/processors/image_processor.py`**:
  * `load_and_validate_image(file_path: Path) -> dict`: Checks format and uncorrupted load via `PIL.Image.open().load()`.
  * `preprocess_image(file_path: Path, output_path: Optional[Path] = None) -> PIL.Image`:
    * Applies `ImageOps.exif_transpose()`.
    * Converts to grayscale: `image.convert("L")`.
    * Applies `ImageOps.autocontrast()`.
  * `process_image(file_path: Path) -> dict`: Preprocesses and saves to `IMAGE_PROCESSED_DIR / "{stem}_processed.png"`.
* **`src/processors/word_processor.py`**:
  * `extract_word_content(file_path: Path) -> list[dict]`:
    * Iterates `docx.Document(file_path).paragraphs` -> `source_type="paragraph"`.
    * Iterates `docx.Document(file_path).tables` -> formats rows with ` | ` delimiters -> `source_type="table"`.
  * `process_word(file_path: Path) -> Generator`: Yields chunks via `process_text_units`.
* **`src/processors/structured_processor.py`**:
  * `extract_structured_data(file_info: dict) -> dict`:
    * For CSV: `{"sheets": {"default": pd.read_csv(file_path)}}`.
    * For Excel: `{"sheets": pd.read_excel(file_path, sheet_name=None)}`.
* **`src/processors/extraction_schema.py`**:
  * Helper factory methods: `create_unified_extraction`, `create_text_source`, `create_structured_source`.

### 3.5 `src/ocr/`
* **`src/ocr/device.py`**:
  * `get_device(preference="auto") -> str`:
    * `"auto"` -> `"cuda"` if `torch.cuda.is_available()` else `"cpu"`.
    * `"cuda"` -> asserts `torch.cuda.is_available()`, raises `RuntimeError` if unavailable.
* **`src/ocr/ocr_utils.py`**:
  * `validate_image_path(image_path) -> Path`: Validates existence and file status.
  * `normalize_ocr_text(text: str) -> str`: Normalizes whitespace via `" ".join(str(text).split())`.
  * `parse_paddle_result(result) -> dict`: Extracts `rec_texts` and `rec_scores`, returns average confidence and newline-delimited text.
  * `create_ocr_record(...) -> dict`.
* **`src/ocr/ocr_engine.py`**:
  * Class `OCREngine(lang="ar")`:
    * Encapsulates `paddleocr.PaddleOCR(lang=lang, enable_mkldnn=False)`.
    * `extract_text(image_path: Path) -> dict`.
* **`src/ocr/handwriting_ocr.py`**:
  * Class `HandwritingOCREngine(device="auto")`:
    * Model: `sherif1313/Arabic-handwritten-OCR-4bit-Qwen2.5-VL-3B-v3`.
    * Backend: `transformers.AutoProcessor` + `transformers.Qwen2_5_VLForConditionalGeneration`.
    * Prompt:
      ```text
      Transcribe all handwritten text in this image exactly as it appears.
      Preserve medicine names, numbers, dosages, units, and instructions.
      Do not add information that is not visible.
      ```
    * `extract_text(image_path: Path) -> dict`.
* **`src/ocr/ocr_router.py`**:
  * Class `OCRRouter(device="auto")`:
    * Implements lazy-initialization for `self.qwen_engine` and `self.printed_engine`.
    * `process(image_path, engine="qwen") -> dict`: Routes to `HandwritingOCREngine` if `"qwen"`, or `OCREngine` if `"paddle"`.

### 3.6 `src/llm/`
* **`src/llm/local_llm.py`**:
  * Class `LocalLLM(model="qwen3:latest", base_url="http://localhost:11434", timeout=600)`:
    * `generate(prompt: str, system_prompt: Optional[str] = None) -> str`:
      * POST to `/api/generate` with payload: `{"model": self.model, "prompt": prompt, "stream": False, "format": "json", "think": False}`.
    * `generate_json(prompt: str, system_prompt: Optional[str] = None) -> dict`: Parses response via `json.loads`.
* **`src/llm/llm_schema.py`**:
  * Complete Pydantic v2 schemas:
    * `LocationData`, `StaffData`, `ClientData`, `MedicalHistoryData`, `VitalData`, `LabResultData`, `MedicationData`, `ServiceData`, `AppointmentData`, `TreatmentRecordData`, `ConsentData`, `PhotoData`, `InvoiceData`, `InvoiceItemData`, `PaymentData`, `PackageData`, `ClientPackageData`, `ProductData`, `SourceDocumentData`.
    * Root Model: `LLMExtractionResult` containing lists for all 19 entities.
* **`src/llm/llm_processor.py`**:
  * Class `LLMProcessor(model="qwen3:latest", base_url="http://localhost:11434", timeout=600)`:
    * `build_prompt(text: str) -> str`: Multi-page detailed medical extraction prompt containing strict rules:
      * Medication Block Demarcation: Medication name starts a block; following text defines dosage/frequency until the next medication starts.
      * Preservation of exact names without translation or normalization.
      * Explicit negative rules: Never invent missing information; return `null` if unclear; return `[]` if table unsupported.
    * `_normalize_numeric_values(data: dict) -> dict`: Casts numeric fields (e.g. `heart_rate`, `temperature`, `weight`, `value`, `duration_min`, `price`, `units`, `subtotal`, `tax`, `total`, `qty`) to `float`/`int`.
    * `_normalize_string_values(data: dict) -> dict`: Strips whitespace, converts empty strings `""` to `None`.
    * `_normalize_dates(data: dict) -> dict`: Normalizes date fields (`dob`, `test_date`, `start_date`, `end_date`, `expiry_date`, `issue_date`) to `%Y-%m-%d`. Normalizes datetime fields (`recorded_at`, `start_at`, `end_at`, `signed_at`, `taken_at`, `paid_at`, `expires_at`) to `%Y-%m-%d %H:%M:%S`.
    * `process(text: str) -> dict`: Coordinates generation -> parse -> normalize -> guard -> pydantic validation -> returns `validated.model_dump()`.

### 3.7 `src/validation/`
* **`src/validation/extraction_guard.py`**:
  * Class `ExtractionGuard`:
    * `apply(data: dict, text: str) -> dict`:
      * Checks if text contains prescription indicators: `["prescription", "rx", "دواء", "ادوية", "روشتة", "علاج", "مرات يوميا", "قطرة", "قرص", "كبسولة", "مرهم", ...]`.
      * If `is_prescription == True`: Atomically sets all tables except `medications` to `[]` (`locations`, `staff`, `clients`, `invoices`, `appointments`, etc.).
      * Cleans out empty entity dictionaries where all values are `None` or `""`.
* **`src/validation/validator.py`**:
  * Class `DataValidator`:
    * `validate(data: dict) -> dict`:
      * Executes `LLMExtractionResult.model_validate(data)`.
      * Returns `{"valid": True, "data": normalized_dict, "errors": []}` or `{"valid": False, "data": None, "errors": formatted_errors_list}`.

### 3.8 `src/database/`
* **`src/database/database.py`**:
  * Class `Database`:
    * Connection: `DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=ZaWolfDB;Trusted_Connection=yes;TrustServerCertificate=yes;`.
    * `connect() -> pyodbc.Connection`
    * `execute(query, params=None)`
    * `insert_and_get_id(query, params=None) -> int`: Executes insert with `OUTPUT INSERTED.id` and commits.
    * `fetch_one(query, params=None) -> tuple`
    * `test_connection() -> str`
* **`src/database/repository.py`**:
  * Class `Repository(table_name: str)`:
    * `insert(data: dict, cursor=None) -> int`: Dynamic parameterized SQL query using `OUTPUT INSERTED.id`. Executes on existing transaction `cursor` if provided, else opens new auto-commit connection.
    * `get_by_id(record_id: int) -> tuple`
* **`src/database/relation_resolver.py`**:
  * Class `RelationResolver`:
    * `find_client(client: dict, cursor=None) -> Optional[int]`: Looks up `id FROM clients WHERE first_name = ? AND last_name = ? AND (mobile = ? OR (? IS NULL AND mobile IS NULL))`.
    * `find_staff(full_name: str, cursor=None) -> Optional[int]`
    * `find_location(name: str, cursor=None) -> Optional[int]`
    * `find_service(name: str, cursor=None) -> Optional[int]`
    * `find_product(name: str, cursor=None) -> Optional[int]`
    * `find_package(name: str, cursor=None) -> Optional[int]`
* **`src/database/mapper.py`**:
  * Class `DatabaseMapper`:
    * `save(data: dict) -> dict`:
      * Manages atomic SQL Server transaction via `connection = self.db.connect()`, `cursor = connection.cursor()`.
      * Insertion Sequence (Dependency Graph):
        1. `locations` -> `_insert_simple`
        2. `staff` -> resolves `location_name` to `location_id`
        3. `clients` -> stores inserted IDs in `client_ids`
        4. `medical_history`, `vitals`, `lab_results`, `medications` -> attaches `client_id` (if available; `medications` allowed without client_id for raw prescriptions)
        5. `services`, `packages`, `products` -> `_insert_simple`
        6. `appointments` -> resolves `client_name` / `staff_name` / `location_name` / `service_name` to FKs
        7. `treatment_records` -> resolves `product_name` to `product_id`, attaches `appointment_id`
        8. `consents` -> attaches `client_id`
        9. `photos` -> attaches `client_id` and `treatment_id`
        10. `invoices` -> attaches `client_id` and `appointment_id`
        11. `invoice_items` -> attaches `invoice_id` (asserts invoice exists)
        12. `payments` -> attaches `invoice_id` (asserts invoice exists)
        13. `client_packages` -> resolves `package_name` to `package_id`, attaches `client_id`
        14. `source_documents` -> stores original file metadata and extraction JSON
      * On any failure: `connection.rollback()` and re-raises exception.
      * On success: `connection.commit()` and returns dictionary of inserted IDs per table.

### 3.9 `src/pipeline.py`
* Class `ProcessingPipeline(ocr_engine="qwen")`:
  * Core orchestrator orchestrating ingestion, routing, processing, OCR, LLM extraction, validation, and database persistence.
  * Methods:
    * `process_file(file_path: Union[str, Path]) -> dict`:
      * Detects file -> Routes -> Calls sub-pipeline.
      * Handles Digital PDF batching and intermediate validation.
      * Handles Scanned PDF page-rendering and OCR aggregation with confidence averaging.
      * Handles Word extraction via DOM text units.
      * Handles Structured CSV/Excel files returning sheet summary metadata.
      * Returns standardized output: `{"status": "valid"|"invalid"|"unsupported"|"error", "data": ..., "source_text": ..., "ocr_text": ..., "source_metadata": ..., "errors": [...]}`.
    * `process_and_save_file(file_path: Union[str, Path]) -> dict`:
      * Calls `process_file(file_path)`.
      * Appends `_build_source_document` record to `data["source_documents"]`.
      * Calls `DatabaseMapper.save(data)`.
      * Returns: `{"status": "saved", "data": data, "inserted": inserted_ids_dict, "errors": []}`.
    * `process_text(text: str) -> dict`: Direct string pipeline (LLM -> Validator).
    * `process_and_save(text: str) -> dict`: Direct string pipeline with DB save.

---

## 4. RELATIONAL SCHEMA & DATABASE TOPOLOGY (19 TABLES)

```text
locations (id PK, name, address, phone)
    ▲
    ├──────────────────────────┐
    │ location_id              │ location_id
staff (id PK, full_name, role, license_no, location_id FK, is_active)
    ▲
    │ staff_id
appointments (id PK, client_id FK, staff_id FK, location_id FK, service_id FK, room, start_at, end_at, status, notes)
    ▲                                              │
    │ appointment_id                               │ service_id
    ├──────────────────────────┬───────────────────┼──────────────────────────┐
    │ appointment_id           │ appointment_id    │                          │ appointment_id
treatment_records              invoices            services (id PK, ...)     consents (id PK, client_id FK, appointment_id FK, ...)
(id PK, appointment_id FK,     (id PK, client_id FK, appointment_id FK, ...)
product_id FK, ...)            ▲
    ▲                          ├──────────────────────────┐
    │ treatment_id             │ invoice_id               │ invoice_id
photos                         invoice_items              payments
(id PK, client_id FK,          (id PK, invoice_id FK,     (id PK, invoice_id FK,
treatment_id FK, ...)          item_type, item_id, ...)   amount, method, paid_at, ...)

clients (id PK, first_name, last_name, dob, gender, mobile, email, address, lead_source, medical_alerts, opt_in_sms)
    ▲
    ├─ medical_history (id PK, client_id FK, type, name, notes, recorded_at)
    ├─ vitals (id PK, client_id FK, blood_pressure, heart_rate, temperature, weight, recorded_at)
    ├─ lab_results (id PK, client_id FK, test_name, value, unit, reference_range, test_date)
    ├─ medications (id PK, client_id FK [NULLABLE], medication_name, dosage, frequency, start_date, end_date)
    ├─ client_packages (id PK, client_id FK, package_id FK, remaining_sessions, expires_at)
    └─ (consents, photos, invoices, appointments)

Independent Catalogs:
- packages (id PK, name, sessions_count, price, validity_days)
- products (id PK, name, brand, type, unit, stock_qty, cost, price)
- source_documents (id PK, file_name, doc_type, ocr_text, llm_json, confidence, review_status)
```

---

## 5. PIPELINE RETURN CONTRACTS

Every public method in `ProcessingPipeline` returns a dictionary conforming to this contract:

```typescript
// TypeScript Contract Representation for LLM Reasoning
interface PipelineResult {
  status: "saved" | "valid" | "invalid" | "unsupported" | "error";
  data: LLMExtractionResult | null;
  structured_data?: {
    file_name: string;
    file_type: "excel" | "csv";
    content_type: "structured";
    sheets: Record<string, any>; // pandas DataFrames
  } | null;
  structured_summary?: Record<string, {
    rows: number;
    columns: number;
    column_names: string[];
  }> | null;
  inserted?: Record<string, number[]>; // Table name to array of inserted IDs
  source_text: string;
  ocr_text: string;
  source_metadata: {
    file_name?: string;
    route?: string;
    ocr_engine?: "qwen" | "paddle" | null;
    ocr_confidence?: number | null;
  };
  errors: Array<{
    type: string;
    message?: string;
    field?: string;
    batch?: number;
  }>;
}
```

---

## 6. INSTRUCTIONS FOR CONTINUATION & SYSTEM MODIFICATION

When tasked with reading, modifying, or extending `ZaWolf_project`:

1. **Retain Pydantic Schema Synchronization:** Any new medical fields added to `src/llm/llm_schema.py` MUST be accompanied by:
   - Corresponding prompt guidance and extraction rules in `src/llm/llm_processor.py`.
   - Table definition in `src/database/mapper.py` (`self.repositories` and corresponding `_insert_*` method).
   - SQL Server table column migration in `ZaWolfDB`.
2. **Preserve Lazy Loading in OCR Router:** Do not import or instantiate `HandwritingOCREngine` (Qwen2.5-VL) globally at module load time; keep it inside `OCRRouter._get_qwen_engine()` to avoid VRAM exhaustion during non-OCR tasks.
3. **Preserve Transactional Scoping:** Never perform raw `cursor.commit()` inside individual repository calls. All commits are orchestrated at the conclusion of `DatabaseMapper.save()` to maintain atomic rollback guarantees.
4. **Preserve Ingestion Neutrality:** Do not inject medical domain logic or filtering into `src/ingestion/` or `src/processors/`. All domain filtering and normalization belongs in `src/llm/` and `src/validation/`.
