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