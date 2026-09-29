from pathlib import Path

import pandas as pd


def extract_structured_data(file_info):
    file_path = Path(file_info["file_path"])
    file_type = file_info["file_type"]

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if file_type == "csv":
        sheets = {
            "default": pd.read_csv(file_path)
        }

    elif file_type == "excel":
        sheets = pd.read_excel(
            file_path,
            sheet_name=None
        )

    else:
        raise ValueError(
            "The provided file is not an Excel or CSV file."
        )

    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_type": file_type,
        "content_type": "structured",
        "sheets": sheets
    }