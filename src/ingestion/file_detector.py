from pathlib import Path

from config.settings import INPUT_DIR, SUPPORTED_EXTENSIONS


def get_input_files():
    return [
        file_path
        for file_path in INPUT_DIR.iterdir()
        if file_path.is_file()
    ]


def detect_file_type(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = file_path.suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(extension)

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "extension": extension,
        "file_type": file_type or "unsupported",
        "supported": file_type is not None
    }