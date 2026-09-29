from pydantic import ValidationError

from src.llm.llm_schema import LLMExtractionResult


class DataValidator:
    def validate(self, data):
        try:
            validated = LLMExtractionResult.model_validate(data)

            normalized_data = validated.model_dump()

            return {
                "valid": True,
                "data": normalized_data,
                "errors": []
            }

        except ValidationError as error:
            return {
                "valid": False,
                "data": None,
                "errors": self._format_errors(error)
            }

    def _format_errors(self, error):
        errors = []

        for item in error.errors():
            location = ".".join(str(part) for part in item["loc"])

            errors.append({
                "field": location,
                "message": item["msg"],
                "type": item["type"]
            })

        return errors