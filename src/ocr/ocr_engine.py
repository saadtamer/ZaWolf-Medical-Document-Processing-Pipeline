import os

os.environ["FLAGS_enable_pir_api"] = "0"

from pathlib import Path
from paddleocr import PaddleOCR

from src.ocr.ocr_utils import (
    validate_image_path,
    parse_paddle_result,
    create_ocr_record
)


class OCREngine:

    def __init__(self, lang="ar"):
        self.lang = lang
        self.engine = PaddleOCR(
            lang=lang,
            enable_mkldnn=False
        )

    def extract_text(self, image_path):
        image_path = validate_image_path(image_path)

        result = self.engine.predict(
            str(image_path)
        )

        parsed_result = parse_paddle_result(result)

        return create_ocr_record(
            file_name=image_path.name,
            source_type="image",
            source_number=1,
            text=parsed_result["text"],
            ocr_engine="PaddleOCR",
            language=self.lang,
            confidence=parsed_result["confidence"]
        )