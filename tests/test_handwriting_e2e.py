from pathlib import Path

from src.pipeline import ProcessingPipeline


def main():
    project_root = Path(__file__).resolve().parents[1]
    image_path = project_root / "data" / "input" / "hand_write.jpg"

    print(f"Testing: {image_path}")
    print("-" * 80)

    pipeline = ProcessingPipeline(ocr_engine="qwen")

    result = pipeline.process_and_save_file(image_path)

    print(result)


if __name__ == "__main__":
    main()