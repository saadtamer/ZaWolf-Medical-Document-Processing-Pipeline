# ZaWolf Project Context

## 1. Project Identity

Project Name:
ZaWolf_project

Project Type:
Medical / Hospital Document Processing and OCR System

Project Goal:
Build a modular medical document processing system that accepts different
document formats, extracts their content, processes images when required,
uses OCR for image-based documents, uses an LLM to organize and standardize
the extracted information, validates the final structured output, and stores
the validated data in a database.

Project Root:
E:\ZaWolf_project


# 2. Main System Architecture

The fixed architecture is:

Input File
    ↓
File Extension Detection
    ↓
Router
    ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
PDF            Image          Excel/CSV      Word
↓              ↓              ↓              ↓
Digital/       Image          Direct Data    Direct Text
Scanned
↓       ↓
Text    Images
↓       ↓
└───────┴─────────────────────────────────────┐
                                              ↓
                                             OCR
                                              ↓
                                      Text Processing
                                              ↓
                                             LLM
                                              ↓
                                         Validation
                                      ↙             ↘
                                   Valid           Invalid
                                     ↓               ↓
                                 Database      Reprocess/Review
                                     ↓
                                  Production


# 3. Important Architecture Rules

These rules must NOT be changed without discussing the change first.

1. File type detection is rule-based using file extensions.
2. Router decides which processor handles each input type.
3. Scanned PDF pages are converted to images.
4. Scanned PDF images use the SAME Image/OCR branch.
5. There is NO separate OCR architecture for scanned PDFs.
6. Images are processed generically before OCR.
7. Excel and CSV do NOT use OCR.
8. Word documents do NOT use OCR.
9. Digital PDFs are processed directly as text.
10. OCR is responsible for converting image content into text.
11. LLM is shared after extraction/OCR.
12. LLM organizes, cleans, standardizes, and maps extracted information.
13. LLM must NOT invent missing information.
14. Missing values must be preserved during extraction.
15. Data cleaning is NOT performed inside Excel/CSV extraction.
16. Data quality analysis is NOT performed during raw extraction.
17. Validation happens after LLM processing.
18. Invalid data goes to reprocessing/review.
19. Database is the final storage layer.
20. System must remain modular.
21. OCR is intentionally being implemented AFTER the input-processing layer.
22. Do not add unnecessary features before the current stage is complete.


# 4. Supported Input Types

Currently supported:

- PDF
- JPG
- JPEG
- PNG
- WEBP
- XLSX
- XLS
- CSV
- DOCX

Old `.doc` binary Word files are NOT currently supported by python-docx.


# 5. Project Structure

E:\ZaWolf_project

├── .venv/
├── data/
│   ├── input/
│   ├── processed/
│   └── output/
├── models/
├── logs/
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── file_detector.py
│   │   └── router.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   ├── word_processor.py
│   │   ├── structured_processor.py
│   │   └── image_processor.py
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── ocr_engine.py
│   │   └── ocr_utils.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── llm_processor.py
│   ├── validation/
│   │   ├── __init__.py
│   │   └── validator.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── database.py
│   ├── pipeline.py
│   └── utils.py
├── tests/
│   └── __init__.py
├── main.py
├── .env
├── .gitignore
├── requirements.txt
├── medical_document_processing.ipynb
└── PROJECT_CONTEXT.md


# 6. Completed Stages

## 6.1 File Ingestion

Status: COMPLETED

Implemented:

- Input directory scanning
- File existence checking
- File extension detection
- Supported/unsupported file identification


## 6.2 File Routing

Status: COMPLETED

Implemented:

- PDF route
- Image route
- Excel route
- CSV route
- Word route
- Unsupported route


## 6.3 PDF Processing

Status: COMPLETED

Implemented:

- PDF type detection
- Digital PDF detection
- Scanned PDF detection
- Digital PDF text extraction
- Text chunking
- Scanned PDF page-to-image conversion

Important:

Scanned PDF does NOT go directly to a separate OCR processor.

It becomes images and enters the Image/OCR branch.


## 6.4 Image Processing

Status: COMPLETED

Implemented:

- File existence validation
- Image extension validation
- Image corruption validation
- Image loading
- EXIF orientation correction
- Grayscale conversion
- Auto contrast
- Processed image saving
- Processing result metadata


## 6.5 Excel / CSV Processing

Status: COMPLETED

Implemented:

- CSV loading using pandas
- Excel workbook loading using pandas
- Multiple Excel sheets support
- DataFrame-based representation
- Missing values preserved

Important:

No cleaning is performed during extraction.

No duplicate analysis is performed.

No missing-value analysis is performed.

No data-quality analysis is performed.


## 6.6 Word Processing

Status: COMPLETED

Implemented:

- DOCX validation
- Paragraph extraction
- Table extraction
- Text representation of tables
- Text batching
- Text chunking


## 6.7 Basic Pipeline Integration

Status: COMPLETED

The pipeline currently connects:

File Detection
→ Routing
→ PDF Processor
→ Image Processor
→ Word Processor
→ Structured Processor

The pipeline has been executed successfully.


# 7. Current Stage

CURRENT STAGE:

OCR

Current position:

Input Processing is complete.

The next development stage is OCR.

Do NOT skip directly to LLM, Validation, or Database.


# 8. Text Processing / Chunking Status

Status:

PARTIALLY COMPLETED

Already implemented for:

- Digital PDF text
- Word text

Existing concepts:

- RecursiveCharacterTextSplitter
- Chunk size
- Chunk overlap
- Dynamic batching
- Memory-aware batching

OCR output should later enter the same text-processing flow where appropriate.

Do not create an unnecessary separate chunking architecture for OCR.


# 9. Pipeline / Orchestration Status

Status:

BASIC INTEGRATION COMPLETED

Current pipeline can:

- Detect files
- Route files
- Process PDFs
- Convert scanned PDF pages to images
- Process images
- Process Word files
- Process Excel/CSV files

The current pipeline still needs later integration with:

- OCR
- LLM
- Validation
- Database
- Error handling
- Production orchestration


# 10. OCR Requirements

OCR must be evaluated based on the following requirements:

1. Arabic
2. English
3. Arabic + English mixed
4. Handwritten text when required
5. Medical terminology
6. Numbers
7. Dosage
8. Units
9. CER evaluation
10. WER evaluation
11. Real hospital-like images
12. Fine-tuning capability
13. Local deployment option

Potential OCR technologies/models may be researched later.

No final OCR model has been selected yet.

OCR selection must be based on actual project requirements and evaluation,
not popularity alone.


# 11. OCR Development Plan

The OCR stage should follow this order:

1. Define OCR input/output contract
2. Research candidate OCR engines/models
3. Compare candidates against project requirements
4. Select OCR engine/model
5. Implement OCR engine
6. Support Arabic
7. Support English
8. Support mixed Arabic/English
9. Handle numbers and dosage/units
10. Investigate handwriting support
11. Evaluate medical terminology
12. Evaluate CER
13. Evaluate WER
14. Test on hospital-like images
15. Investigate fine-tuning if needed
16. Verify local deployment capability
17. Integrate OCR into the pipeline


# 12. LLM Stage

Status:

NOT STARTED

Purpose:

The LLM will receive extracted/OCR text and organize it into the required
medical structure.

Responsibilities:

- Understand extracted content
- Clean text when appropriate
- Standardize values
- Map information to required fields
- Organize unstructured medical information
- Preserve information that exists
- Avoid inventing missing information

The LLM must NOT replace OCR.

OCR extracts text.

LLM interprets and structures text.


# 13. Validation Stage

Status:

NOT STARTED

Purpose:

Validate the LLM output before database storage.

Expected validation areas:

- Required fields
- Data types
- Schema compliance
- Allowed values
- Structural consistency
- Invalid output detection

Pydantic may be used if appropriate.

Invalid results should go to:

Reprocess / Review


# 14. Database Stage

Status:

NOT STARTED

Purpose:

Store validated structured medical data.

Database integration will be implemented after:

OCR
→ Text Processing
→ LLM
→ Validation


# 15. Error Handling / Reprocessing

Status:

NOT STARTED

Future behavior:

Invalid extraction or invalid structured output should be handled through
controlled reprocessing or human review.

Do not silently discard medical information.


# 16. Testing

Status:

BASIC TESTING COMPLETED

Confirmed:

- Pipeline executes successfully
- Multiple input types were processed
- PDF processing works
- Scanned PDF pages can be converted to images
- Image loading/validation works
- Pipeline completed successfully with test input files

Current test result:

Pipeline completed successfully with 4 input files.

Known warning:

The current PDF processor uses the deprecated `fitz` API.

Warning:

`The fitz API is deprecated and will be removed in future.`

This is a warning, not a pipeline failure.

It can be cleaned later by migrating to `pymupdf` imports.


# 17. Environment

Python:

3.11.9

Project environment:

`.venv`

Main installed dependencies include:

- Pillow
- PyMuPDF
- python-docx
- pandas
- openpyxl
- psutil
- langchain-text-splitters


# 18. Configuration

Important configuration is located in:

config/settings.py

Current concepts include:

- PROJECT_ROOT
- DATA_DIR
- INPUT_DIR
- PROCESSED_DIR
- OUTPUT_DIR
- MODELS_DIR
- LOGS_DIR
- MAX_BATCH_TEXT_SIZE
- BATCH_MEMORY_SAFETY_RATIO
- SUPPORTED_IMAGE_EXTENSIONS
- SUPPORTED_EXTENSIONS
- IMAGE_PROCESSED_DIR
- PDF_IMAGES_DIR


# 19. Git / Repository

Repository:

ZaWolf_project

Branch:

main

Remote repository:

github.com/saadtamer/ZaWolf_project

Important:

Do NOT commit:

- `.env`
- `.venv`
- medical patient data
- real hospital documents
- secrets
- API keys
- large local models
- logs
- generated temporary files


# 20. Development Rules

When continuing the project:

1. Always check the current stage before modifying code.
2. Do not redo completed stages unnecessarily.
3. Do not change the architecture without discussing why.
4. Do not introduce unnecessary libraries.
5. Keep processors modular.
6. Keep OCR independent from the generic image processor.
7. Do not put OCR logic inside PDF processor.
8. Do not put OCR logic inside Image Processor.
9. Scanned PDF images must use the same OCR path as normal images.
10. Preserve raw extracted information.
11. Do not invent missing medical information.
12. Do not perform unnecessary data cleaning during ingestion.
13. Keep extraction separate from interpretation.
14. Keep validation separate from LLM processing.
15. Keep database storage separate from processing.
16. Prefer simple, maintainable implementations.
17. Finish the current stage before expanding scope.


# 21. Current Project Roadmap

[COMPLETED]
1. Input / File Ingestion
2. File Routing
3. PDF Processing
4. Image Processing
5. Excel / CSV Processing
6. Word Processing
7. Basic Pipeline Integration

[PARTIAL]
8. Text Processing / Chunking
9. Pipeline / Orchestration

[NEXT]
10. OCR

[TODO]
11. LLM Processing
12. Validation
13. Database
14. Error Handling / Reprocessing
15. Full Testing
16. Deployment / Production


# 22. Current Development Instruction

When the user says:

"نكمل ZaWolf"

Start from the CURRENT STAGE recorded in this file.

Current stage:

OCR

Do not restart the project.

Do not redesign the architecture unless there is a clear technical reason.

First determine what is already implemented in the current OCR files before
adding new code.


# 23. Change Log

## Current checkpoint

Input Processing Layer completed.

Pipeline successfully executed.

Next target:
OCR architecture and implementation.

Do not move to LLM until OCR integration is completed.