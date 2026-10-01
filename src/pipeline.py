from pathlib import Path
import json

import pandas as pd

from src.ingestion.file_detector import detect_file_type
from src.ingestion.router import route_file

from src.processors.pdf_processor import (
    detect_pdf_type,
    process_pdf_to_chunks,
    convert_pdf_to_images,
)

from src.processors.word_processor import process_word
from src.processors.structured_processor import extract_structured_data
from src.processors.image_processor import process_image

from src.ocr.ocr_router import OCRRouter

from src.llm.llm_processor import LLMProcessor
from src.validation.validator import DataValidator
from src.database.mapper import DatabaseMapper

from config.settings import PROCESSED_DIR


class ProcessingPipeline:

    def __init__(self, ocr_engine="auto"):
        self.llm_processor = LLMProcessor()
        self.validator = DataValidator()
        self.database_mapper = DatabaseMapper()

        self.ocr_router = OCRRouter()
        self.ocr_engine = ocr_engine

    def process_file(self, file_path):

        try:
            file_info = detect_file_type(file_path)

            if not file_info["supported"]:
                return {
                    "status": "unsupported",
                    "data": None,
                    "source_text": "",
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "unsupported_file",
                            "message": (
                                f"Unsupported file type: "
                                f"{file_info.get('extension')}"
                            ),
                        }
                    ],
                }

            route = route_file(file_info)

            if route == "pdf_pipeline":
                return self._process_pdf_file(file_info)

            if route in [
                "excel_pipeline",
                "csv_pipeline",
            ]:
                return self._process_structured_file(
                    file_info
                )

            if route == "word_pipeline":
                return self._process_word_file(
                    file_info
                )

            text = self._extract_text(
                file_info,
                route,
            )

            if not text.strip():
                return {
                    "status": "invalid",
                    "data": None,
                    "source_text": "",
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "empty_text",
                            "message": (
                                "No text extracted from file."
                            ),
                        }
                    ],
                }

            result = self.process_text(text)

            if result["status"] == "valid":
                result["source_text"] = text

                if route == "image_pipeline":
                    result["ocr_text"] = text
                else:
                    result["ocr_text"] = ""

                result["source_metadata"] = {
                    "file_name": Path(
                        file_info["file_path"]
                    ).name,
                    "route": route,
                    "ocr_engine": (
                        self.ocr_engine
                        if route == "image_pipeline"
                        else None
                    ),
                }

            return result

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": "pipeline_error",
                        "message": str(error),
                    }
                ],
            }

        finally:
            if hasattr(self, "llm_processor") and self.llm_processor:
                try:
                    self.llm_processor.close()
                except Exception:
                    pass

    def process_and_save_file(self, file_path):

        result = self.process_file(
            file_path
        )

        if result["status"] != "valid":
            return result

        if result.get("structured_data") is not None:

            return {
                "status": "valid",
                "data": result.get("data"),
                "structured_data": result.get(
                    "structured_data"
                ),
                "structured_summary": result.get(
                    "structured_summary"
                ),
                "inserted": {},
                "errors": [],
            }

        try:

            data = result["data"]

            source_metadata = result.get(
                "source_metadata",
                {},
            )

            source_text = result.get(
                "source_text",
                "",
            )

            ocr_text = result.get(
                "ocr_text",
                "",
            )

            source_document = (
                self._build_source_document(
                    file_path=file_path,
                    data=data,
                    source_metadata=source_metadata,
                    source_text=source_text,
                    ocr_text=ocr_text,
                )
            )

            if source_document:

                data = data.copy()

                source_documents = list(
                    data.get(
                        "source_documents",
                        [],
                    )
                )

                source_documents.append(
                    source_document
                )

                data["source_documents"] = (
                    source_documents
                )

            inserted = self.database_mapper.save(
                data
            )

            return {
                "status": "saved",
                "data": data,
                "inserted": inserted,
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": result.get("data"),
                "inserted": {},
                "errors": [
                    {
                        "type": "database_error",
                        "message": str(error),
                    }
                ],
            }

    def process_text(self, text):

        try:

            llm_data = self.llm_processor.process(
                text
            )

            validation_result = (
                self.validator.validate(
                    llm_data
                )
            )

            if not validation_result["valid"]:

                return {
                    "status": "invalid",
                    "data": validation_result.get(
                        "data"
                    ),
                    "source_text": text,
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": (
                        validation_result.get(
                            "errors",
                            [],
                        )
                    ),
                }

            return {
                "status": "valid",
                "data": validation_result["data"],
                "source_text": text,
                "ocr_text": "",
                "source_metadata": {},
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "source_text": text,
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": "text_processing_error",
                        "message": str(error),
                    }
                ],
            }

    def process_and_save(self, text):

        result = self.process_text(
            text
        )

        if result["status"] != "valid":
            return result

        try:

            data = result["data"]

            inserted = self.database_mapper.save(
                data
            )

            return {
                "status": "saved",
                "data": data,
                "inserted": inserted,
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": result["data"],
                "inserted": {},
                "errors": [
                    {
                        "type": "database_error",
                        "message": str(error),
                    }
                ],
            }

    def _extract_text(
        self,
        file_info,
        route,
    ):

        file_path = Path(
            file_info["file_path"]
        )

        if route == "word_pipeline":
            return self._process_word(
                file_path
            )

        if route in [
            "excel_pipeline",
            "csv_pipeline",
        ]:
            raise ValueError(
                "Structured files must be processed "
                "through _process_structured_file()."
            )

        if route == "image_pipeline":
            return self._process_image(
                file_path
            )

        raise ValueError(
            f"Unsupported route: {route}"
        )

    def _process_word(
        self,
        file_path,
    ):

        result = process_word(
            file_path
        )

        text_parts = []

        for batch in result:

            if not isinstance(
                batch,
                list,
            ):
                continue

            for chunk in batch:

                if not isinstance(
                    chunk,
                    dict,
                ):
                    continue

                text = chunk.get(
                    "text"
                )

                if text:
                    text_parts.append(
                        text
                    )

        return "\n\n".join(
            text_parts
        )

    def _process_word_file(
        self,
        file_info,
    ):
        file_path = Path(
            file_info["file_path"]
        )

        merged_data = (
            self._create_empty_data()
        )

        batch_count = 0
        text_parts = []

        for batch in process_word(file_path):
            batch_text = "\n\n".join(
                chunk["text"]
                for chunk in batch
                if isinstance(chunk, dict) and chunk.get("text")
            )

            if not batch_text.strip():
                continue

            batch_count += 1
            print(f"       ↳ Processing Word batch {batch_count}...", flush=True)
            text_parts.append(batch_text)

            batch_result = self.process_text(
                batch_text
            )

            if batch_result["status"] != "valid":
                return {
                    "status": batch_result["status"],
                    "data": None,
                    "source_text": "\n\n".join(text_parts),
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "word_batch_error",
                            "batch": batch_count,
                            "errors": batch_result.get("errors", []),
                        }
                    ],
                }

            merged_data = self._merge_extracted_data(
                merged_data,
                batch_result["data"],
            )

        if batch_count == 0:
            return {
                "status": "invalid",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": "empty_word_document",
                        "message": "No text extracted from Word document.",
                    }
                ],
            }

        validation_result = self.validator.validate(
            merged_data
        )

        if not validation_result["valid"]:
            return {
                "status": "invalid",
                "data": validation_result.get("data"),
                "source_text": "\n\n".join(text_parts),
                "ocr_text": "",
                "source_metadata": {},
                "errors": validation_result.get("errors", []),
            }

        return {
            "status": "valid",
            "data": validation_result["data"],
            "source_text": "\n\n".join(text_parts),
            "ocr_text": "",
            "source_metadata": {
                "file_name": file_path.name,
                "route": "word_pipeline",
                "ocr_engine": None,
            },
            "errors": [],
        }

    def _process_structured_file(
        self,
        file_info,
    ):

        try:

            structured_data = (
                extract_structured_data(
                    file_info
                )
            )

            if not structured_data:

                return {
                    "status": "invalid",
                    "data": None,
                    "structured_data": None,
                    "structured_summary": None,
                    "errors": [
                        {
                            "type": (
                                "empty_structured_data"
                            ),
                            "message": (
                                "No structured data "
                                "extracted."
                            ),
                        }
                    ],
                }

            sheets = structured_data.get(
                "sheets",
                {},
            )

            if not sheets:

                return {
                    "status": "invalid",
                    "data": None,
                    "structured_data": (
                        structured_data
                    ),
                    "structured_summary": None,
                    "errors": [
                        {
                            "type": "empty_sheets",
                            "message": (
                                "No sheets found "
                                "in structured file."
                            ),
                        }
                    ],
                }

            sheet_summary = {}

            for (
                sheet_name,
                dataframe,
            ) in sheets.items():

                if not isinstance(
                    dataframe,
                    pd.DataFrame,
                ):

                    return {
                        "status": "invalid",
                        "data": None,
                        "structured_data": (
                            structured_data
                        ),
                        "structured_summary": None,
                        "errors": [
                            {
                                "type": (
                                    "invalid_sheet_data"
                                ),
                                "message": (
                                    f"Sheet '{sheet_name}' "
                                    "does not contain a "
                                    "pandas DataFrame."
                                ),
                            }
                        ],
                    }

                sheet_summary[
                    sheet_name
                ] = {
                    "rows": len(
                        dataframe
                    ),
                    "columns": len(
                        dataframe.columns
                    ),
                    "column_names": (
                        dataframe.columns.tolist()
                    ),
                }

            return {
                "status": "valid",
                "data": self._create_empty_data(),
                "structured_data": (
                    structured_data
                ),
                "structured_summary": (
                    sheet_summary
                ),
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {
                    "file_name": Path(
                        file_info["file_path"]
                    ).name,
                    "route": "structured",
                    "ocr_engine": None,
                },
                "errors": [],
            }

        except Exception as error:

            return {
                "status": "error",
                "data": None,
                "structured_data": None,
                "structured_summary": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "structured_processing_error"
                        ),
                        "message": str(error),
                    }
                ],
            }

    def _process_image(
        self,
        file_path,
    ):

        processed_image = process_image(
            file_path
        )

        if isinstance(
            processed_image,
            dict,
        ):

            image_path = (
                processed_image.get(
                    "processed_path"
                )
            )

            if image_path:

                ocr_result = (
                    self.ocr_router.process(
                        image_path,
                        engine=self.ocr_engine,
                        is_scanned_pdf=False,
                    )
                )

            else:

                ocr_result = (
                    self.ocr_router.process(
                        file_path,
                        engine=self.ocr_engine,
                        is_scanned_pdf=False,
                    )
                )

        else:

            ocr_result = (
                self.ocr_router.process(
                    processed_image,
                    engine=self.ocr_engine,
                    is_scanned_pdf=False,
                )
            )

        if not ocr_result.get("text"):
            return ""

        return ocr_result["text"]

    def _process_pdf_file(
        self,
        file_info,
    ):

        file_path = Path(
            file_info["file_path"]
        )

        pdf_info = detect_pdf_type(
            file_path
        )

        if pdf_info["pdf_type"] == "digital":

            return self._process_digital_pdf(
                file_path
            )

        return self._process_scanned_pdf(
            file_path
        )

    def _process_digital_pdf(
        self,
        file_path,
    ):

        merged_data = (
            self._create_empty_data()
        )

        batch_count = 0
        text_parts = []

        for batch_chunks in process_pdf_to_chunks(
            file_path
        ):

            batch_text = "\n\n".join(
                chunk["text"]
                for chunk in batch_chunks
                if chunk.get("text")
            )

            if not batch_text.strip():
                continue

            batch_count += 1
            print(f"       ↳ Processing PDF batch {batch_count}...", flush=True)

            text_parts.append(
                batch_text
            )

            batch_result = self.process_text(
                batch_text
            )

            if batch_result["status"] != "valid":

                return {
                    "status": (
                        batch_result["status"]
                    ),
                    "data": None,
                    "source_text": (
                        "\n\n".join(
                            text_parts
                        )
                    ),
                    "ocr_text": "",
                    "source_metadata": {},
                    "errors": [
                        {
                            "type": "pdf_batch_error",
                            "batch": batch_count,
                            "errors": (
                                batch_result[
                                    "errors"
                                ]
                            ),
                        }
                    ],
                }

            merged_data = (
                self._merge_extracted_data(
                    merged_data,
                    batch_result["data"],
                )
            )

        if batch_count == 0:

            return {
                "status": "invalid",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "empty_digital_pdf"
                        ),
                        "message": (
                            "No text batches were "
                            "extracted from the "
                            "digital PDF."
                        ),
                    }
                ],
            }

        validation_result = (
            self.validator.validate(
                merged_data
            )
        )

        if not validation_result["valid"]:

            return {
                "status": "invalid",
                "data": validation_result.get(
                    "data"
                ),
                "source_text": (
                    "\n\n".join(
                        text_parts
                    )
                ),
                "ocr_text": "",
                "source_metadata": {},
                "errors": (
                    validation_result.get(
                        "errors",
                        [],
                    )
                ),
            }

        return {
            "status": "valid",
            "data": validation_result["data"],
            "source_text": (
                "\n\n".join(
                    text_parts
                )
            ),
            "ocr_text": "",
            "source_metadata": {
                "file_name": file_path.name,
                "route": "digital_pdf",
                "ocr_engine": None,
            },
            "errors": [],
        }

    def _process_scanned_pdf(
        self,
        file_path,
    ):

        output_dir = (
            Path(PROCESSED_DIR)
            / "pdf_images"
        )

        text_parts = []
        confidence_values = []

        for page in convert_pdf_to_images(
            file_path,
            output_dir,
        ):

            ocr_result = (
                self.ocr_router.process(
                    page["image_path"],
                    engine=self.ocr_engine,
                    is_scanned_pdf=True,
                )
            )

            page_text = ocr_result.get(
                "text",
                "",
            )

            if page_text:
                text_parts.append(
                    page_text
                )

            confidence = ocr_result.get(
                "confidence"
            )

            if isinstance(
                confidence,
                (int, float),
            ):
                confidence_values.append(
                    float(confidence)
                )

        text = "\n\n".join(
            text_parts
        )

        if not text.strip():

            return {
                "status": "invalid",
                "data": None,
                "source_text": "",
                "ocr_text": "",
                "source_metadata": {},
                "errors": [
                    {
                        "type": (
                            "empty_scanned_pdf"
                        ),
                        "message": (
                            "No text extracted "
                            "from scanned PDF."
                        ),
                    }
                ],
            }

        result = self.process_text(
            text
        )

        if result["status"] != "valid":
            return result

        average_confidence = None

        if confidence_values:

            average_confidence = (
                sum(confidence_values)
                / len(confidence_values)
            )

        result["source_text"] = text
        result["ocr_text"] = text

        result["source_metadata"] = {
            "file_name": file_path.name,
            "route": "scanned_pdf",
            "ocr_engine": self.ocr_engine,
            "ocr_confidence": (
                average_confidence
            ),
        }

        return result

    def _build_source_document(
        self,
        file_path,
        data,
        source_metadata,
        source_text,
        ocr_text,
    ):

        file_path = Path(
            file_path
        )

        route = source_metadata.get(
            "route",
            "",
        )

        if route == "structured":
            return None

        if route == "image_pipeline":

            doc_type = "image"

        elif route == "digital_pdf":

            doc_type = "digital_pdf"

        elif route == "scanned_pdf":

            doc_type = "scanned_pdf"

        elif route == "word_pipeline":

            doc_type = "word"

        else:

            doc_type = (
                route
                or file_path.suffix.lower()
            )

        return {
            "file_name": file_path.name,
            "doc_type": doc_type,
            "ocr_text": (
                ocr_text
                if ocr_text
                else None
            ),
            "llm_json": json.dumps(
                data,
                ensure_ascii=False,
                default=str,
            ),
            "review_status": "auto_processed",
        }

    def _create_empty_data(self):

        return {
            "locations": [],
            "staff": [],
            "clients": [],
            "medical_history": [],
            "vitals": [],
            "lab_results": [],
            "medications": [],
            "services": [],
            "appointments": [],
            "treatment_records": [],
            "consents": [],
            "photos": [],
            "invoices": [],
            "invoice_items": [],
            "payments": [],
            "packages": [],
            "client_packages": [],
            "products": [],
            "source_documents": [],
        }

    def _merge_extracted_data(
        self,
        merged_data,
        batch_data,
    ):

        for table in merged_data:

            records = batch_data.get(
                table,
                [],
            )

            if not isinstance(
                records,
                list,
            ):
                continue

            merged_data[
                table
            ].extend(records)

        return merged_data