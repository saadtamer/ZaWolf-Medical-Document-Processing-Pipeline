<div align="center">

# 🐺 ZaWolf Medical Document Processing Pipeline
### **Enterprise On-Premise Clinical Document Extraction, Multimodal Vision OCR & Relational SQL Server Persistence**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQL Server](https://img.shields.io/badge/SQL_Server-2022-CC292B?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://microsoft.com/sql-server)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Qwen2.5-VL](https://img.shields.io/badge/VLM-Qwen2.5--VL--3B-6366F1?style=for-the-badge)](https://huggingface.co/Qwen)
[![PaddleOCR](https://img.shields.io/badge/OCR-PaddleOCR-148F77?style=for-the-badge)](https://github.com/PaddlePaddle/PaddleOCR)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,2,2,5,30&height=180&section=header&text=ZaWolf%20Clinical%20Document%20Pipeline&fontSize=32&fontColor=ffffff&animation=fadeIn" width="100%"/>

</div>

---

## 🏥 Overview
**ZaWolf** is a production-grade, on-premise clinical data extraction and transactional persistence pipeline engineered by **Eng. Saad Tamer**. It is designed specifically for healthcare organizations, medical clinics, and hospital networks to ingest heterogeneous, unstructured medical records (Digital PDFs, Scanned PDFs, handwritten prescriptions, lab sheets, Word clinical summaries, Excel tables) and reliably transform them into validated relational entities across **19 SQL Server tables** within a single atomic transaction.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    A["Raw Medical Files (PDF, Scanned, DOCX, CSV, JPG)"] --> B["File Ingestion & Route Detector"]
    
    B -->|"Digital PDF"| C1["PyMuPDF Contextual Chunker + psutil Memory Guard"]
    B -->|"Scanned PDF / Printed Images"| C2["PaddleOCR Engine (Arabic & English)"]
    B -->|"Handwritten Prescriptions"| C3["Qwen2.5-VL-3B Vision Language Model"]
    B -->|"Structured Tables (CSV/XLSX)"| C4["Pandas Parser & Tabular Metadata"]
    B -->|"Word Reports (.docx)"| C5["python-docx Paragraph & Table Normalizer"]
    
    C1 & C2 & C3 & C5 --> D["Local LLM Extraction (Ollama / Qwen3-8B)"]
    
    D --> E["ExtractionGuard (Hallucination Prevention)"]
    E --> F["Pydantic v2 Strict Schema Validation"]
    
    F --> G["Database Mapper & Foreign-Key Normalizer"]
    G --> H[("19 Relational SQL Server Tables (ZaWolfDB) - Atomic Commit / Rollback")]
```

---

## ✨ Key Features & Engineering Breakthroughs

* ⚡ **Zero-Data-Leakage On-Premise Execution:** Operates 100% locally with Ollama (`qwen3`) and local HuggingFace transformers (`Qwen2.5-VL-3B`), ensuring strict compliance with patient privacy (HIPAA/GDPR).
* 📑 **Multi-Format Ingestion Engine:**
  * **Digital PDFs:** Contextual chunking with sliding token windows and `psutil` memory usage monitoring.
  * **Scanned PDFs:** Dynamic DPI image rasterization with multi-page batch OCR.
  * **Handwritten Prescriptions:** Deep handwriting deciphering powered by `Qwen2.5-VL-3B-Instruct`.
  * **Office & Tabular Records:** Native parsing for Word (`.docx`), CSV, and Excel (`.xlsx`).
* 🛡️ **ExtractionGuard Anti-Hallucination Barrier:** Strict post-processing layer that zeroes out unmentioned clinical entities, preventing the LLM from fabricating patient names, doctors, or unrelated diagnoses.
* 💾 **Atomic Relational Persistence:** Single-transaction unit-of-work across 19 foreign-key-interlocked tables with complete rollback guarantees on error.

---

## 🗄️ Relational Database Schema (19 Tables)

| Domain | Database Tables |
|---|---|
| **Organizational** | `locations`, `staff` |
| **Patient Profile** | `clients`, `medical_history`, `vitals` |
| **Diagnostics & Labs** | `lab_results`, `treatment_records`, `photos` |
| **Pharmacy & Medications** | `medications`, `products` |
| **Clinical Services & Operations** | `services`, `appointments`, `consents`, `packages`, `client_packages` |
| **Billing & Finance** | `invoices`, `invoice_items`, `payments` |
| **Traceability & Audit** | `source_documents` |

---

## 🚀 Quick Start

### 1. Prerequisites
* Python 3.11+
* Microsoft SQL Server 2019+
* Ollama installed and running (`ollama serve` with `qwen3`)

### 2. Installation
```bash
git clone https://github.com/saadtamer/ZaWolf-Medical-Document-Processing-Pipeline.git
cd ZaWolf-Medical-Document-Processing-Pipeline
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Pipeline
```bash
python main.py --file data/input/sample_prescription.jpg
```

---

<div align="center">
Developed with ❤️ by <b>Eng. Saad Tamer</b> | AI & Data Engineer
</div>
