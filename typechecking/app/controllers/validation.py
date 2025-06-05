from datetime import datetime
from typing import Dict
from fastapi import UploadFile
from app.controllers.mongo import get_active_schema, validate_data_parallel
from app.services.file_processor import FileProcessor


async def validate_file_against_schema(
    file: UploadFile, 
    import_name: str, 
    n_workers: int = 4
) -> Dict:
    """
    Validate an uploaded file against its corresponding JSON schema.
    
    Args:
        file (UploadFile): The file to validate.
        import_name (str): The name of the import to get the schema for.
        n_workers (int): Number of worker threads for parallel validation.
    
    Returns:
        Dict: Validation results containing success status, statistics, and errors.
    """
    # Get the active schema for the import
    schema = get_active_schema(import_name)
    if not schema:
        return {
            "success": False,
            "error": f"No active schema found for import name: {import_name}",
            "validation_results": None
        }
    
    # Process the uploaded file using FileProcessor service
    file_processed, data, error_message = await FileProcessor.process_file(file)
    if not file_processed:
        return {
            "success": False,
            "error": error_message,
            "validation_results": None
        }
    
    if not data:
        return {
            "success": True,
            "error": None,
            "validation_results": {
                "is_valid": True,
                "total_items": 0,
                "valid_items": 0,
                "invalid_items": 0,
                "errors": [],
                "message": "File is empty but valid"
            }
        }
    
    # Validate data against schema
    validation_results = validate_data_parallel(data, schema, n_workers)
    
    # Add file metadata to results
    file_info = FileProcessor.get_file_info(file)
    validation_results.update({
        "file_name": file_info["filename"],
        "file_size": file_info["size"],
        "content_type": file_info["content_type"],
        "import_name": import_name,
        "validated_at": datetime.now().isoformat()
    })
    
    return {
        "success": True,
        "error": None,
        "validation_results": validation_results
    }


def get_validation_summary(validation_results: Dict) -> Dict:
    """
    Generate a summary of validation results.
    
    Args:
        validation_results (Dict): The validation results from validate_file_against_schema.
    
    Returns:
        Dict: A summary of the validation results.
    """
    if not validation_results.get("validation_results"):
        return {
            "status": "error",
            "summary": "No validation results available"
        }
    
    results = validation_results["validation_results"]
    
    if results["is_valid"]:
        status = "success"
        summary = f"All {results['total_items']} items passed validation"
    else:
        status = "warning"
        summary = f"{results['invalid_items']} out of {results['total_items']} items failed validation"
    
    return {
        "status": status,
        "summary": summary,
        "details": {
            "total_items": results["total_items"],
            "valid_items": results["valid_items"],
            "invalid_items": results["invalid_items"],
            "error_count": len(results.get("errors", [])),
            "file_name": results.get("file_name"),
            "validated_at": results.get("validated_at")
        }
    }
