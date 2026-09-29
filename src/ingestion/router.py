def route_file(file_info):
    file_type = file_info["file_type"]

    routes = {
        "pdf": "pdf_pipeline",
        "image": "image_pipeline",
        "excel": "excel_pipeline",
        "csv": "csv_pipeline",
        "word": "word_pipeline"
    }

    return routes.get(file_type, "unsupported")