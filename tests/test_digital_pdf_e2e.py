from pathlib import Path

import fitz

from src.pipeline import ProcessingPipeline


def main():
    project_root = Path(__file__).resolve().parents[1]

    source_pdf = (
        project_root
        / "data"
        / "input"
        / "1.-Introduction-to-machine-learning-Author-Nils-J.-Nilsson.pdf"
    )

    test_pdf = (
        project_root
        / "data"
        / "processed"
        / "digital_pdf_test_5_pages.pdf"
    )

    test_pdf.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    source = fitz.open(source_pdf)
    output = fitz.open()

    try:
        output.insert_pdf(
            source,
            from_page=0,
            to_page=4,
        )

        output.save(test_pdf)

    finally:
        output.close()
        source.close()

    print(f"Testing: {test_pdf}")
    print("-" * 80)

    pipeline = ProcessingPipeline()

    result = pipeline.process_file(
        test_pdf
    )

    print("STATUS:", result["status"])
    print("ERRORS:", result["errors"])

    if result["data"]:
        print(
            "DATA COUNTS:",
            {
                key: len(value)
                for key, value in result["data"].items()
            },
        )

    print("-" * 80)


if __name__ == "__main__":
    main()