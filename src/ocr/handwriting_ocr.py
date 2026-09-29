from pathlib import Path

import torch
from PIL import Image
from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration
)


class HandwritingOCREngine:

    def __init__(self, device="auto"):
        self.device = self._get_device(device)

        self.model_name = (
            "sherif1313/"
            "Arabic-handwritten-OCR-4bit-Qwen2.5-VL-3B-v3"
        )

        self.processor = AutoProcessor.from_pretrained(
            self.model_name
        )

        if self.device == "cuda":
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map="cuda"
            )
        else:
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_name,
                device_map="cpu"
            )

        self.model.eval()

    @staticmethod
    def _get_device(device):
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"

        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA requested but no CUDA GPU is available."
            )

        if device not in ["cuda", "cpu"]:
            raise ValueError(
                "Device must be 'auto', 'cuda', or 'cpu'."
            )

        return device

    def extract_text(self, image_path):
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not image_path.is_file():
            raise ValueError(
                f"Path is not a file: {image_path}"
            )

        image = Image.open(image_path).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe all handwritten text in this image "
                            "exactly as it appears. Preserve medicine names, "
                            "numbers, dosages, units, and instructions. "
                            "Do not add information that is not visible."
                        )
                    }
                ]
            }
        ]

        text_prompt = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.processor(
            text=[text_prompt],
            images=[image],
            return_tensors="pt"
        )

        target_device = torch.device(self.device)

        inputs = {
            key: value.to(target_device)
            if hasattr(value, "to")
            else value
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=512
            )

        input_length = inputs["input_ids"].shape[1]

        generated_text = self.processor.batch_decode(
            generated_ids[:, input_length:],
            skip_special_tokens=True
        )[0].strip()

        return {
            "file_name": image_path.name,
            "source_type": "image",
            "source_number": 1,
            "ocr_engine": "Qwen2.5-VL-3B-Handwriting-OCR",
            "language": "ar/en",
            "text": generated_text,
            "device": self.device,
            "status": "success"
        }