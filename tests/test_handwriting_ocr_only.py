from pathlib import Path

from src.ocr.handwriting_ocr import HandwritingOCREngine


def main():
    project_root = Path(__file__).resolve().parents[1]

    image_path = (
        project_root
        / "data"
        / "input"
        / "hand_write.jpg"
    )

    print(f"Testing: {image_path}")
    print("-" * 80)

    engine = HandwritingOCREngine(device="auto")

    result = engine.extract_text(image_path)

    print("\nOCR RESULT:")
    print("-" * 80)
    print(result["text"])
    print("-" * 80)

    print("\nFULL RESULT:")
    print(result)


if __name__ == "__main__":
    main()