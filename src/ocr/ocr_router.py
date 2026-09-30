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

    def process(self, image_path, engine="auto", is_scanned_pdf=False):
        if engine == "paddle":
            return self._get_printed_engine().extract_text(image_path)

        if engine == "qwen":
            return self._get_qwen_engine().extract_text(image_path)

        if engine == "auto":
            # Pages from multi-page scanned PDFs default to PaddleOCR for high throughput
            if is_scanned_pdf:
                return self._get_printed_engine().extract_text(image_path)

            # Standalone images: fast check with printed OCR pass
            printed_result = self._get_printed_engine().extract_text(image_path)
            text = printed_result.get("text", "").strip()
            confidence = printed_result.get("confidence", 0.0)

            # If substantial printed text is detected with solid confidence, return it immediately
            if len(text) >= 40 and confidence >= 0.70:
                return printed_result

            # If text is sparse, low-confidence, or handwritten prescription, route to Qwen-VL
            try:
                qwen_result = self._get_qwen_engine().extract_text(image_path)
                qwen_text = qwen_result.get("text", "").strip()
                if qwen_text:
                    return qwen_result
            except Exception:
                pass

            return printed_result

        raise ValueError(
            "Engine must be 'auto', 'qwen', or 'paddle'."
        )