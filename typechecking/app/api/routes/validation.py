from app.schemas.api import ApiResponse
from app.controllers.validation import validate_file_against_schema, get_validation_summary
from fastapi import APIRouter, UploadFile, HTTPException


router = APIRouter()


@router.post("/validate")
async def validate(spreadsheet_file: UploadFile, import_name: str) -> ApiResponse:
    """
    Endpoint to validate a spreadsheet file with its jsonschema.

    This endpoint accepts a file upload and an import name, and returns the validation result.
    Args:
        spreadsheet_file (UploadFile): The file to validate.
        import_name (str): The name of the import, used to identify the schema.

    Returns:
        ApiResponse: A dictionary containing the validation result.
    """
    try:
        # Validate the file against the schema
        validation_result = await validate_file_against_schema(
            file=spreadsheet_file,
            import_name=import_name,
            n_workers=4  # You can make this configurable
        )
        
        if not validation_result["success"]:
            return ApiResponse(
                status="error",
                code=400,
                message=validation_result["error"],
                data=None
            )
        
        # Get validation summary
        summary = get_validation_summary(validation_result)
        
        # Determine response based on validation results
        validation_data = validation_result["validation_results"]
        
        if validation_data["is_valid"]:
            return ApiResponse(
                status="success",
                code=200,
                message=f"File validation completed successfully. {summary['summary']}",
                data={
                    "validation_summary": summary,
                    "validation_details": validation_data
                }
            )
        else:
            return ApiResponse(
                status="warning",
                code=200,
                message=f"File validation completed with errors. {summary['summary']}",
                data={
                    "validation_summary": summary,
                    "validation_details": validation_data
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during validation: {str(e)}"
        )
