import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc

from src.pipeline import ProcessingPipeline
from src.database.database import Database

app = FastAPI(
    title="ZaWolf Medical Document Processing API",
    description="Enterprise On-Premise Clinical Document Extraction, Multimodal Vision OCR & SQL Server Persistence API",
    version="2.0.0"
)

# Enable CORS for frontend/mobile apps (React, Flutter, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = ProcessingPipeline(ocr_engine="auto")
db = Database()


class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    database_name: str
    ocr_engine_default: str
    llm_model: str


class ProcessResponse(BaseModel):
    file_name: str
    status: str
    processing_time_seconds: float
    inserted_ids: Dict[str, Any]
    errors: List[Any]
    extracted_data: Optional[Dict[str, Any]] = None


@app.get("/", tags=["General"])
def root():
    return {
        "system": "ZaWolf Medical Document Processing Pipeline",
        "version": "2.0.0",
        "developer": "Eng. Saad Tamer",
        "documentation": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    db_ok = False
    db_name = "Unavailable"
    try:
        db_name = db.test_connection()
        db_ok = True
    except Exception as e:
        db_name = f"Error: {e}"

    return {
        "status": "healthy" if db_ok else "degraded",
        "database_connected": db_ok,
        "database_name": db_name,
        "ocr_engine_default": pipeline.ocr_engine,
        "llm_model": pipeline.llm_processor.llm.model
    }


@app.post("/api/v1/process", response_model=ProcessResponse, tags=["Pipeline"])
async def process_document(
    file: UploadFile = File(...),
    ocr_engine: str = Query("auto", description="OCR Engine: 'auto', 'paddle', or 'qwen'")
):
    """
    Ingests and processes any medical document (Digital PDF, Scanned PDF, Word, Excel, CSV, or Image),
    extracts structured clinical entities via local LLM / OCR, and atomically persists data to SQL Server.
    """
    if ocr_engine not in ["auto", "paddle", "qwen"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ocr_engine must be 'auto', 'paddle', or 'qwen'"
        )

    pipeline.ocr_engine = ocr_engine
    
    # Save uploaded file to a temporary location
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        shutil.copyfileobj(file.file, temp_file)

    start_time = time.perf_counter()
    try:
        result = pipeline.process_and_save_file(temp_path)
        elapsed = time.perf_counter() - start_time

        return {
            "file_name": file.filename,
            "status": result.get("status", "unknown"),
            "processing_time_seconds": round(elapsed, 2),
            "inserted_ids": result.get("inserted", {}),
            "errors": result.get("errors", []),
            "extracted_data": result.get("data")
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        # Cleanup temporary file
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/api/v1/documents", tags=["Audit & Documents"])
def list_recent_documents(limit: int = Query(20, ge=1, le=100)):
    """Fetches recently processed documents from the source_documents audit table."""
    try:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP {limit} id, file_name, doc_type, review_status, created_at 
            FROM source_documents 
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        docs = []
        for r in rows:
            docs.append({
                "id": r[0],
                "file_name": r[1],
                "doc_type": r[2],
                "review_status": r[3],
                "created_at": str(r[4])
            })
        return {"total": len(docs), "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/api/v1/metrics", tags=["Metrics & Statistics"])
def get_system_metrics():
    """Returns real-time database record counts across core medical tables."""
    tables = ["clients", "medications", "vitals", "medical_history", "locations", "services", "source_documents"]
    counts = {}
    try:
        conn = db.connect()
        cursor = conn.cursor()
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
            counts[t] = cursor.fetchone()[0]
        return {"database": "ZaWolfDB", "table_counts": counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            conn.close()
        except Exception:
            pass
