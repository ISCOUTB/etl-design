from fastapi import APIRouter
from app.schemas.api import ApiResponse
from app.messaging.publishers import ValidationPublisher

router = APIRouter()
publisher = ValidationPublisher()


@router.post("/{import_name}/upload")
async def upload_schema(import_name: str, schema: dict) -> ApiResponse:
    """
    Upload a schema for validation.
    This endpoint allows users to upload a JSON schema for validation purposes.
    It checks if the schema is the same as the active schema in the database.
    If it is the same, no update is made. If it is different, the schema is saved
    as the active schema and added to the schemas_releases.
    """
    try:
        task_id = publisher.publish_schema_update(
            schema=schema, import_name=import_name
        )

        return ApiResponse(
            status="accepted",
            code=202,
            message="Schema upload request submitted successfully",
            data={"task_id": task_id},
        )
    except Exception as e:
        return ApiResponse(
            status="error", code=500, message=f"Failed to upload schema: {str(e)}"
        )
