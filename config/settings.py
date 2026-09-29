from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
IMAGE_PROCESSED_DIR = PROCESSED_DIR / "images"
PDF_IMAGES_DIR = PROCESSED_DIR / "pdf_images"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"


MAX_BATCH_TEXT_SIZE = 12000

BATCH_MEMORY_SAFETY_RATIO = 0.25


SUPPORTED_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
]


SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".webp": "image",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".docx": "word",
}