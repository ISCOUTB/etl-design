from fastapi import APIRouter
from app.schemas.api import ApiResponse
from app.controllers.mongo import save_schema


router = APIRouter()


@router.post("/{import_name}/upload")
def upload_schema(import_name: str, schema: dict) -> ApiResponse:
    """
    Upload a schema for validation.
    This endpoint allows users to upload a JSON schema for validation purposes.
    It checks if the schema is the same as the active schema in the database.
    If it is the same, no update is made. If it is different, the schema is saved
    as the active schema and added to the schemas_releases.
    """
    result = save_schema(schema, import_name)
    if result is None:
        return ApiResponse(
            status="error",
            code=400,
            message="Schema is the same as the active schema, no update needed.",
            data=None,
        )

    data = {"import_name": import_name, "schema": schema, "result": result}

    return ApiResponse(
        status="success",
        code=201,
        message="Schema uploaded successfully.",
        data=data,
    )
