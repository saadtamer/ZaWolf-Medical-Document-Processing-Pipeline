import os
import sys
import time
from pathlib import Path

# Force UTF-8 encoding for clean terminal output in Windows
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import ProcessingPipeline

INPUT_DIR = PROJECT_ROOT / "data" / "input"


def format_inserted(inserted_dict):
    """Summarizes non-empty inserted IDs."""
    if not isinstance(inserted_dict, dict):
        return "None"
    items = [f"{table}: {len(ids)}" for table, ids in inserted_dict.items() if ids]
    return ", ".join(items) if items else "Audit Only (source_documents)"


def main():
    print("=" * 85)
    print("🐺 ZAWOLF INPUT DATASET EVALUATION & BENCHMARK SUITE")
    print(f"📁 Target Directory: {INPUT_DIR}")
    print("=" * 85)

    if not INPUT_DIR.exists():
        print(f"❌ Error: Directory not found: {INPUT_DIR}")
        return

    # Collect all supported files
    supported_extensions = {".pdf", ".docx", ".csv", ".xlsx", ".png", ".jpg", ".jpeg"}
    files = [
        p for p in sorted(INPUT_DIR.iterdir())
        if p.is_file() and p.suffix.lower() in supported_extensions
    ]

    total_files = len(files)
    print(f"Found {total_files} files ready for evaluation.\n")

    # Initialize pipeline with auto-adaptive OCR routing and physical core thread detection
    pipeline = ProcessingPipeline(ocr_engine="auto")

    eval_results = []

    for index, file_path in enumerate(files, start=1):
        print("-" * 85, flush=True)
        print(f"[{index}/{total_files}] Processing: {file_path.name}", flush=True)
        print(f"     Type: {file_path.suffix.upper()} | Size: {file_path.stat().st_size / 1024:.1f} KB", flush=True)

        start_time = time.perf_counter()
        try:
            result = pipeline.process_and_save_file(file_path)
            elapsed = time.perf_counter() - start_time

            status = result.get("status", "unknown")
            inserted = result.get("inserted", {})
            errors = result.get("errors", [])
            data = result.get("data") or {}

            # Evaluation verdict
            is_success = status in ["saved", "valid"]
            verdict = "PASS ✅" if is_success else "FAIL ❌"

            # Count extracted entities
            entity_summary = []
            for key, val in data.items():
                if isinstance(val, list) and val:
                    entity_summary.append(f"{key}: {len(val)}")

            print(f"     Result  : {verdict} (Status: {status})", flush=True)
            print(f"     Latency : {elapsed:.2f} seconds", flush=True)
            print(f"     Database: {format_inserted(inserted)}", flush=True)
            if entity_summary:
                print(f"     Entities: {', '.join(entity_summary)}", flush=True)
            if errors:
                print(f"     Errors  : {errors}", flush=True)

            eval_results.append({
                "file": file_path.name,
                "type": file_path.suffix.lower(),
                "status": status,
                "verdict": verdict,
                "elapsed": elapsed,
                "inserted_count": sum(len(ids) for ids in inserted.values() if isinstance(ids, list)),
                "has_errors": bool(errors)
            })

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            print(f"     Result  : FAIL ❌ (Exception: {str(e)})")
            print(f"     Latency : {elapsed:.2f} seconds")
            eval_results.append({
                "file": file_path.name,
                "type": file_path.suffix.lower(),
                "status": "exception",
                "verdict": "FAIL ❌",
                "elapsed": elapsed,
                "inserted_count": 0,
                "has_errors": True
            })

    # Print Final Evaluation Dashboard
    print("\n" + "=" * 85, flush=True)
    print("📊 FINAL EVALUATION & PERFORMANCE DASHBOARD", flush=True)
    print("=" * 85, flush=True)
    print(f"{'#':<3} | {'File Name':<35} | {'Verdict':<8} | {'Status':<7} | {'Time (s)':<8}", flush=True)
    print("-" * 85, flush=True)

    passed_count = 0
    total_time = 0.0

    for idx, r in enumerate(eval_results, start=1):
        file_display = r['file'][:33] + ".." if len(r['file']) > 35 else r['file']
        print(f"{idx:<3} | {file_display:<35} | {r['verdict']:<8} | {r['status']:<7} | {r['elapsed']:<8.2f}", flush=True)
        if "PASS" in r['verdict']:
            passed_count += 1
        total_time += r['elapsed']

    print("=" * 85, flush=True)
    print(f"Total Evaluated: {total_files} files", flush=True)
    print(f"Passed         : {passed_count} / {total_files} ({passed_count / total_files * 100:.1f}%)", flush=True)
    print(f"Failed         : {total_files - passed_count}", flush=True)
    print(f"Total Time     : {total_time:.2f} seconds", flush=True)
    if total_files > 0:
        print(f"Average Time   : {total_time / total_files:.2f} s/file", flush=True)
    print("=" * 85, flush=True)

    # Save to CSV for reporting
    try:
        import pandas as pd
        out_csv = PROJECT_ROOT / "data" / "output" / "evaluation_input_results.csv"
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(eval_results).to_csv(out_csv, index=False, encoding="utf-8-sig")
        print(f"💾 Results saved to: {out_csv}", flush=True)
    except Exception as save_err:
        print(f"⚠️ Warning: Could not save CSV report: {save_err}", flush=True)


if __name__ == "__main__":
    main()
