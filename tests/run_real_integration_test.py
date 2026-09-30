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