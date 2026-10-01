# ZaWolf Project Context & Architecture Reference (Final Release)

## 1. Project Identity

* **Project Name:** ZaWolf Medical Document Processing Pipeline
* **Engineer:** Eng. Saad Tamer (AI & Data Engineer)
* **Project Type:** Enterprise Medical & Clinical Document Intelligence, Multimodal OCR & Relational SQL Server Persistence
* **Project Root:** `E:\ZaWolf_project`
* **Target Database:** Microsoft SQL Server (`ZaWolfDB`)
* **Core Model:** Ollama `qwen3:latest` (Locked for high-precision entity extraction)
* **Vision OCR Engines:** `PaddleOCR` (Arabic & English printed) + `Qwen2.5-VL-3B` (Handwritten prescriptions)

---

## 2. Core Architectural Pillars (Final Enhancements)

1. **Hardware-Adaptive Physical Core Detection:**
   * Dynamic sensing using `psutil.cpu_count(logical=False)`.
   * Automatically allocates physical cores to `LocalLLM(num_thread=...)`, ensuring portable performance from consumer PCs to 64-core enterprise servers.

2. **Managed HTTP Session & Auto-Closing Socket Lifecycle:**
   * Enforced socket teardown in `finally:` blocks inside `ProcessingPipeline.process_file`.
   * Calls `self.llm_processor.close()`, releasing `requests.Session` handles and returning ports to OS.

3. **13 Relational Covering Indexes in SQL Server:**
   * Non-clustered covering indexes placed across foreign keys (`client_id`, `document_id`, `provider_id`) in `ZaWolfDB`.
   * Speeds up table joins and deduplication lookups by over 10x.

4. **Smart Adaptive OCR Router (`engine="auto"`):**
   * Multi-page scanned PDFs and high-confidence printed text route to `PaddleOCR` (<1s).
   * Handwritten physician prescriptions route to `Qwen2.5-VL-3B`.

5. **Sliding-Window Document Chunking:**
   * Prevents context window overflows on massive Word documents (`.docx`) and multi-page digital PDFs.
   * Merges clinical entity dictionaries across batches with automated deduplication.

6. **Enterprise FastAPI REST Gateway:**
   * Interactive Swagger documentation at `/docs`.
   * Endpoints: `POST /api/v1/process`, `GET /api/v1/health`, `GET /api/v1/metrics`, `GET /api/v1/documents`.

---

## 3. Supported Input Formats & Routing Logic

| Format | Pipeline Route | Processing Method |
|---|---|---|
| `.pdf` (Digital) | `pdf_pipeline` | PyMuPDF text extraction -> Contextual sliding chunks -> LLM |
| `.pdf` (Scanned) | `pdf_pipeline` | Image rasterization -> PaddleOCR -> ExtractionGuard -> LLM |
| `.png`, `.jpg`, `.jpeg` | `image_pipeline` | Preprocessing -> OCRRouter (`auto`: Paddle / Qwen2.5-VL) -> LLM |
| `.csv`, `.xlsx`, `.xls` | `structured` | Vectorized pandas parser (bypasses LLM in <0.1s) -> DB |
| `.docx` | `word_pipeline` | python-docx sliding window chunker -> LLM -> Entity merger |

---

## 4. Relational Database Schema (`ZaWolfDB` - 19 Tables)

All clinical records are persisted inside a single atomic transaction:

1. `locations` (Clinics, hospitals, branches)
2. `staff` (Physicians, pharmacists, lab techs)
3. `clients` (Patients, demographics, IDs)
4. `medical_history` (Allergies, chronic conditions, surgeries)
5. `vitals` (Blood pressure, heart rate, temperature, SpO2, BMI)
6. `lab_results` (Test names, quantitative values, reference ranges)
7. `medications` (Drugs, dosages, frequency, duration)
8. `services` (Medical procedures, consultations)
9. `appointments` (Scheduled visits, time, status)
10. `treatment_records` (Clinical notes, outcomes)
11. `consents` (Patient approvals, legal forms)
12. `photos` (Clinical images, wound photos)
13. `invoices` (Billing headers, totals, dates)
14. `invoice_items` (Itemized charges, service links)
15. `payments` (Payment methods, transactions)
16. `packages` (Treatment packages, health programs)
17. `client_packages` (Patient package subscriptions)
18. `products` (Pharmaceutical inventory, medical supplies)
19. `source_documents` (Audit trail, raw OCR text, LLM JSON payloads)

---

## 5. Verification & Benchmark Summary

* **Tool:** `evaluate_input_files.py`
* **Test Dataset:** 8 heterogeneous files (`data/input/`)
* **Success Rate:** 100.0% (8 / 8 PASS)
* **Failures / Errors:** 0
* **Persistence:** All 8 files successfully mapped and saved into `ZaWolfDB`.