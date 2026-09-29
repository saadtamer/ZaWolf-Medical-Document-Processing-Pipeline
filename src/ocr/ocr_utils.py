from pathlib import Path


def validate_image_path(image_path):
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            f"Path is not a file: {image_path}"
        )

    return image_path


def normalize_ocr_text(text):
    if text is None:
        return ""

    return " ".join(str(text).split())


def parse_paddle_result(result):
    texts = []
    scores = []

    for page_result in result:
        data = page_result

        if hasattr(data, "rec_texts"):
            texts.extend(data.rec_texts)
            scores.extend(data.rec_scores)

        elif isinstance(data, dict):
            texts.extend(data.get("rec_texts", []))
            scores.extend(data.get("rec_scores", []))

    clean_texts = [
        normalize_ocr_text(text)
        for text in texts
        if normalize_ocr_text(text)
    ]

    valid_scores = [
        float(score)
        for score in scores
        if score is not None
    ]

    full_text = "\n".join(clean_texts)

    confidence = (
        sum(valid_scores) / len(valid_scores)
        if valid_scores
        else 0.0
    )

    return {
        "text": full_text,
        "confidence": confidence
    }



def create_ocr_record(
    file_name,
    source_type,
    source_number,
    text,
    ocr_engine,
    language="ar",
    confidence=0.0
):
    return {
        "file_name": file_name,
        "source_type": source_type,
        "source_number": source_number,
        "ocr_engine": ocr_engine,
        "language": language,
        "text": normalize_ocr_text(text),
        "confidence": confidence,
        "status": "success"
    }