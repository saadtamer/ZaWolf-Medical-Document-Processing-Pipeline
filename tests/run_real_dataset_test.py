import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import ProcessingPipeline

root = PROJECT_ROOT / "real_test"

files = []

for folder in ["handwritten", "images"]:
    folder_files = sorted(
        [f for f in (root / folder).iterdir() if f.is_file()]
    )[:5]
    files.extend(folder_files)

files.extend(sorted((root / "csv").glob("*")))
files.extend(sorted((root / "docx").glob("*")))
files.extend(sorted((root / "pdf").glob("*")))

print(f"TOTAL FILES: {len(files)}")
print("=" * 70)

pipeline = ProcessingPipeline(ocr_engine="qwen")
results = []

for index, file_path in enumerate(files, 1):
    print(f"[{index}/{len(files)}] {file_path}", flush=True)

    try:
        result = pipeline.process_file(file_path)
        status = result.get("status", "unknown")
        results.append((file_path, status))
        print(f"    STATUS: {status}", flush=True)

    except Exception as error:
        results.append((file_path, "error"))
        print(f"    ERROR: {error}", flush=True)

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

summary = {}

for file_path, status in results:
    summary[status] = summary.get(status, 0) + 1

for status, count in summary.items():
    print(f"{status}: {count}")

print(f"TOTAL PROCESSED: {len(results)}")
