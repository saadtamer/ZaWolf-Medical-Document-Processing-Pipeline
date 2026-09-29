from src.ocr.ocr_engine import OCREngine
from src.ocr.handwriting_ocr import HandwritingOCREngine
from src.ocr.device import get_device


class OCRRouter:

    def __init__(self, device="auto"):
        self.device = get_device(device)
        self.qwen_engine = None
        self.printed_engine = None

    def _get_qwen_engine(self):
        if self.qwen_engine is None:
            self.qwen_engine = HandwritingOCREngine(
                device=self.device
            )

        return self.qwen_engine

    def _get_printed_engine(self):
        if self.printed_engine is None:
            self.printed_engine = OCREngine(lang="ar")

        return self.printed_engine

    def process(self, image_path, engine="qwen"):
        if engine == "qwen":
            return self._get_qwen_engine().extract_text(image_path)

        if engine == "paddle":
            return self._get_printed_engine().extract_text(image_path)

        raise ValueError(
            "Engine must be 'qwen' or 'paddle'."
        )