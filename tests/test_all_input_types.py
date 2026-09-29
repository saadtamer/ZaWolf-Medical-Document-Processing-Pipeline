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

    for input_type, file_path in TEST_FILES.items():
        print("=" * 80)
        print(f"TEST: {input_type}")
        print(f"FILE: {file_path}")

        if not file_path.exists():
            results[input_type] = {
                "status": "missing",
                "errors": [f"File not found: {file_path}"],
            }
            print("STATUS: missing")
            continue

        result = pipeline.process_file(file_path)

        results[input_type] = {
            "status": result["status"],
            "errors": result["errors"],
        }

        print("STATUS:", result["status"])
        print("ERRORS:", result["errors"])

        if result.get("data") is not None:
            print(
                "DATA COUNTS:",
                {
                    key: len(value)
                    for key, value in result["data"].items()
                    if isinstance(value, list)
                },
            )

        if result.get("structured_summary") is not None:
            print("STRUCTURED SUMMARY:", result["structured_summary"])

    print("\n")
    print("=" * 80)
    print("FINAL INPUT TYPE TEST REPORT")
    print("=" * 80)

    passed = 0
    failed = 0

    for input_type, result in results.items():
        status = result["status"]

        if status == "valid":
            print(f"[PASS] {input_type}")
            passed += 1
        else:
            print(f"[FAIL] {input_type} -> {status}")
            print("       Errors:", result["errors"])
            failed += 1

    print("=" * 80)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"TOTAL:  {len(results)}")
    print("=" * 80)

    if failed == 0:
        print("ALL INPUT TYPES PASSED")


if __name__ == "__main__":
    main()