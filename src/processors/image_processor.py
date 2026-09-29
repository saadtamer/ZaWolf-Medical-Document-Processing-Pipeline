from pathlib import Path

from PIL import Image, ImageOps

from config.settings import (
    SUPPORTED_IMAGE_EXTENSIONS,
    IMAGE_PROCESSED_DIR
)


def load_and_validate_image(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            "The provided file is not a supported image format."
        )

    try:
        image = Image.open(file_path)
        image.load()
    except Exception as error:
        raise ValueError(
            f"Invalid or corrupted image: {error}"
        )

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "format": image.format,
        "mode": image.mode,
        "width": image.width,
        "height": image.height
    }


def preprocess_image(file_path, output_path=None):
    file_path = Path(file_path)

    image = Image.open(file_path)
    image.load()

    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageOps.autocontrast(image)

    if output_path is not None:
        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        image.save(output_path)

    return image


def process_image(file_path):
    file_path = Path(file_path)

    load_and_validate_image(file_path)

    output_path = (
        IMAGE_PROCESSED_DIR /
        f"{file_path.stem}_processed.png"
    )

    image = preprocess_image(
        file_path,
        output_path
    )

    return {
        "file_name": file_path.name,
        "file_type": "image",
        "content_type": "image",
        "original_path": str(file_path),
        "processed_path": str(output_path),
        "width": image.width,
        "height": image.height,
        "mode": image.mode
    }