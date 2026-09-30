import csv
import time
from pathlib import Path

from src.pipeline import ProcessingPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_TEST_DIR = PROJECT_ROOT / "real_test"
RESULTS_DIR = REAL_TEST_DIR / "results"
RESULTS_FILE = RESULTS_DIR / "real_dataset_test_results.csv"

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
    ".docx",
    ".csv",
}


def get_files():
    files = []

    for path in REAL_TEST_DIR.rglob("*"):
        if not path.is_file():
            continue

        if "results" in path.parts:
            continue

        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return sorted(files)


def get_file_type(path):
    extension = path.suffix.lower()

    if extension in [".jpg", ".jpeg", ".png"]:
        return "image"

    if extension == ".pdf":
        return "pdf"

    if extension == ".docx":
        return "docx"

    if extension == ".csv":
        return "csv"

    return "unknown"


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    files = get_files()
    total = len(files)

    print("=" * 70)
    print("ZaWolf REAL DATASET TEST")
    print("=" * 70)
    print(f"Total files: {total}")
    print(f"Results: {RESULTS_FILE}")
    print("=" * 70)

    pipeline = ProcessingPipeline(ocr_engine="qwen")

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
                "relative_path",
                "file_type",
                "status",
                "processing_seconds",
                "text_length",
                "error",
            ],
        )

        writer.writeheader()

        success = 0
        errors = 0

        for index, file_path in enumerate(files, start=1):
            file_type = get_file_type(file_path)

            print()
            print(
                f"[{index}/{total}] "
                f"{file_type.upper()} "
                f"{file_path.name}"
            )

            start_time = time.perf_counter()

            try:
                result = pipeline.process_file(file_path)

                elapsed = time.perf_counter() - start_time

                status = result.get("status", "unknown")

                data = result.get("data")
                text_length = 0

                if isinstance(data, dict):
                    text_length = sum(
                        len(str(value))
                        for value in data.values()
                        if value is not None
                    )

                error_message = ""

                if result.get("errors"):
                    error_message = str(result["errors"])

                if status in ["valid", "saved"]:
                    success += 1
                else:
                    errors += 1

                print(
                    f"    Status: {status}"
                )
                print(
                    f"    Time: {elapsed:.2f}s"
                )

                if error_message:
                    print(
                        f"    Error: {error_message}"
                    )

                writer.writerow({
                    "index": index,
                    "total": total,
                    "file_name": file_path.name,
                    "relative_path": str(
                        file_path.relative_to(REAL_TEST_DIR)
                    ),
                    "file_type": file_type,
                    "status": status,
                    "processing_seconds": round(
                        elapsed,
                        2,
                    ),
                    "text_length": text_length,
                    "error": error_message,
                })

                csv_file.flush()

            except KeyboardInterrupt:
                print()
                print("TEST STOPPED BY USER")
                print(
                    f"Completed before stop: "
                    f"{index - 1}/{total}"
                )
                break

            except Exception as error:
                elapsed = time.perf_counter() - start_time
                errors += 1

                error_message = str(error)

                print(
                    f"    Status: exception"
                )
                print(
                    f"    Time: {elapsed:.2f}s"
                )
                print(
                    f"    Error: {error_message}"
                )

                writer.writerow({
                    "index": index,
                    "total": total,
                    "file_name": file_path.name,
                    "relative_path": str(
                        file_path.relative_to(REAL_TEST_DIR)
                    ),
                    "file_type": file_type,
                    "status": "exception",
                    "processing_seconds": round(
                        elapsed,
                        2,
                    ),
                    "text_length": 0,
                    "error": error_message,
                })

                csv_file.flush()

    print()
    print("=" * 70)
    print("REAL DATASET TEST FINISHED")
    print("=" * 70)
    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"Errors: {errors}")
    print(f"Results: {RESULTS_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()