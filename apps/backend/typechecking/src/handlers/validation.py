import multiprocessing as mp
from datetime import datetime
from typing import Any, Dict, List, Tuple

import jsonschema
from fastapi import UploadFile
from proto_utils.database import DatabaseClient, dtypes

from src.core.config import settings
from src.handlers.schemas import get_active_schema
from src.schemas.handlers import (
    SummaryDetails,
    ValidationResult,
    ValidationResults,
    ValidationSummary,
)
from src.services.file_processor import FileProcessor
from src.utils import standardize_string


async def validate_file_against_schema(
    file: UploadFile,
    import_name: str,
    database_client: DatabaseClient,
    n_workers: int = settings.MAX_WORKERS,
) -> ValidationResult:
    """
    Validate an uploaded file against its corresponding JSON schema.

    Args:
        file (UploadFile): The file to validate.
        import_name (str): The name of the import to get the schema for.
        n_workers (int): Number of worker threads for parallel validation.

    Returns:
        Dict: Validation results containing success status, statistics, and errors.
    """
    n_workers = min(n_workers, settings.MAX_WORKERS)

    # Get the active schema for the import
    schema = get_active_schema(import_name, database_client)
    if not schema:
        return {
            "success": False,
            "error": f"No active schema found for import name: {import_name}",
            "validation_results": None,
        }

    # Standardize schema to ensure consistent validation (e.g., handle case sensitivity)
    schema["properties"] = dict(
        map(
            lambda kv: (standardize_string(kv[0]), kv[1]),
            schema.get("properties", {}).items(),
        )
    )
    schema["required"] = list(map(standardize_string, schema.get("required", [])))

    # Process the uploaded file using FileProcessor service
    file_processed, data, error_message = await FileProcessor.process_file(file)
    if not file_processed:
        return {
            "success": False,
            "error": error_message,
            "validation_results": None,
        }

    if not data:
        return ValidationResult(
            success=True,
            error=None,
            validation_results=ValidationResults(
                is_valid=False,
                total_items=0,
                valid_items=0,
                invalid_items=0,
                errors=[],
                message="File is empty but valid",
            ),
        )

    # Verify that the columns in data match the schema properties
    schema_properties = set(schema.get("properties", {}).keys())
    df_columns = set(data[0].keys())

    if df_columns != schema_properties:
        return {
            "success": False,
            "error": (
                "Columns do not match schema properties. "
                f"File columns: {sorted(df_columns)}. "
                f"Schema properties: {sorted(schema_properties)}."
            ),
            "validation_results": None,
        }

    # Try to parse the data types according to schema
    data = _convert_data_types(data, schema)

    # Validate data against schema
    validation_results = validate_data_parallel(data, schema, n_workers)

    # Add file metadata to results
    file_info = FileProcessor.get_file_info(file)
    validation_results.update(
        {
            "file_name": file_info["filename"],
            "file_size": file_info["size"],
            "content_type": file_info["content_type"],
            "import_name": import_name,
            "validated_at": datetime.now().isoformat(),
        }
    )

    return ValidationResult(
        success=True,
        error=None,
        validation_results=validation_results,
    )


def get_validation_summary(
    validation_results: ValidationResult,
) -> ValidationSummary:
    """
    Generate a summary of validation results.

    Args:
        validation_results (Dict): The validation results from validate_file_against_schema.

    Returns:
        Dict: A summary of the validation results.
    """
    if not validation_results.get("validation_results"):
        return ValidationSummary(
            status="error",
            summary="No validation results available",
            details=None,
        )

    results = validation_results["validation_results"]
    if results is None:
        return ValidationSummary(
            status="error",
            summary="Validation results are None",
            details=None,
        )

    if results["is_valid"]:
        status = "success"
        summary = f"All {results['total_items']} items passed validation"
    else:
        status = "warning"
        summary = f"{results['invalid_items']} out of {results['total_items']} items failed validation"

    return ValidationSummary(
        status=status,
        summary=summary,
        details=SummaryDetails(
            total_items=results["total_items"],
            valid_items=results["valid_items"],
            invalid_items=results["invalid_items"],
            error_count=len(results.get("errors", [])),
            file_name=results.get("file_name"),
            validated_at=results.get("validated_at"),
        ),
    )


def validate_chunks(
    args: Tuple[List[Dict], Dict[str, Any], int],
) -> Tuple[int, bool, list[str]]:
    data, schema, chunk_start = args
    errors = []

    for i, item in enumerate(data):
        try:
            jsonschema.validate(instance=item, schema=schema)
        except jsonschema.ValidationError as e:
            # Report spreadsheet line number
            errors.append(f"Item {chunk_start + i + 1}: {str(e)}")

    return chunk_start, len(errors) == 0, errors


def validate_data_parallel(
    data: List[Dict[str, Any]],
    schema: dtypes.JsonSchema,
    n_workers: int = settings.MAX_WORKERS,
) -> ValidationResults:
    """
    Validate data against a JSON schema using parallel processing.

    Args:
        data (List[Dict]): The data to validate.
        schema (dtypes.JsonSchema): The JSON schema to validate against.
        n_workers (int): Number of worker threads to use.

    Returns:
        Dict: A dictionary containing validation results with success status,
              total items, valid items, and error details.
    """
    if not data:
        return ValidationResults(
            is_valid=True,
            total_items=0,
            valid_items=0,
            invalid_items=0,
            errors=[],
            message="File is empty but valid",
        )
    # Convert to JsonSchema standard and allow null values in optional fields.
    required_fields = set(schema.get("required", []))
    converted_properties: Dict[str, Dict[str, Any]] = {}

    for field_name, field_schema in schema.get("properties", {}).items():
        converted_field_schema: Dict[str, Any] = {
            "type": field_schema["type"],
            **field_schema.get("extra", {}),
        }

        if field_name not in required_fields and "type" in converted_field_schema:
            field_type = converted_field_schema["type"]
            if isinstance(field_type, list):
                if "null" not in field_type:
                    converted_field_schema["type"] = [*field_type, "null"]
            elif isinstance(field_type, str) and field_type != "null":
                converted_field_schema["type"] = [field_type, "null"]

        converted_properties[field_name] = converted_field_schema

    schema["properties"] = converted_properties  # type: ignore
    schema_draft = schema.pop("schema", "http://json-schema.org/draft-07/schema#")
    schema["$schema"] = schema_draft  # type: ignore

    # Split data into chunks for parallel processing
    chunk_size = max(1, len(data) // n_workers)
    chunks = list(
        map(
            lambda idx: (
                data[idx : idx + chunk_size],
                schema,
                idx,
            ),
            range(0, len(data), chunk_size),
        )
    )
    chunk_lengths = {
        chunk_start: len(chunk_data) for chunk_data, _, chunk_start in chunks
    }

    actual_processes = min(n_workers, len(chunks))
    with mp.Pool(processes=actual_processes) as pool:
        results = pool.map(validate_chunks, chunks)  # type: ignore

    # Process results
    all_errors = []
    total_valid_items = 0

    for chunk_start, is_valid, errors in results:
        chunk_size_actual = chunk_lengths[chunk_start]
        if is_valid:
            total_valid_items += chunk_size_actual
            continue

        all_errors.extend(errors)
        total_valid_items += chunk_size_actual - len(errors)

    # Keep row-level counters consistent with row-level validation.
    total_items = len(data)
    invalid_items = total_items - total_valid_items

    # Ensure deterministic ordering by the original row index.
    all_errors.sort(
        key=lambda err: int(err.split(":", 1)[0].replace("Item ", ""))
        if err.startswith("Item ")
        else float("inf")
    )

    # Limit errors to first 50 to avoid overwhelming response
    return ValidationResults(
        is_valid=len(all_errors) == 0,
        total_items=total_items,
        valid_items=total_valid_items,
        invalid_items=invalid_items,
        errors=all_errors[:50],
        message=f"{invalid_items} out of {total_items} items failed validation",
    )


def _convert_data_types(
    data: List[Dict[str, Any]], schema: dtypes.JsonSchema
) -> List[Dict[str, Any]]:
    """
    Convert data types according to JSON schema definitions.

    Args:
        data: List of dictionaries representing rows
        schema: JSON schema with type definitions

    Returns:
        List of dictionaries with converted types
    """
    if not data or not schema.get("properties"):
        return data

    properties = schema["properties"]
    converted_data = []

    for row in data:
        converted_row = {}
        for key, value in row.items():
            if key not in properties:
                converted_row[key] = value
                continue

            prop_type = properties[key].get("type")

            try:
                if prop_type == "boolean":
                    # Handle boolean conversion from string representations
                    if isinstance(value, str):
                        if value.lower() in ("true", "1", "yes", "y"):
                            converted_row[key] = True
                        elif value.lower() in ("false", "0", "no", "n"):
                            converted_row[key] = False
                        else:
                            # Keep original value if can't convert
                            converted_row[key] = value
                    else:
                        converted_row[key] = bool(value)

                elif prop_type == "integer":
                    if value is None or value == "":
                        converted_row[key] = None
                    else:
                        converted_row[key] = int(float(str(value)))

                elif prop_type == "number":
                    if value is None or value == "":
                        converted_row[key] = None
                    else:
                        converted_row[key] = float(value)

                elif prop_type == "string":
                    converted_row[key] = str(value) if value is not None else None

                else:
                    # For other types (array, object, etc.), keep as is
                    converted_row[key] = value

            except (ValueError, TypeError):
                # If conversion fails, keep original value for validation to catch error
                converted_row[key] = value

        converted_data.append(converted_row)

    return converted_data
