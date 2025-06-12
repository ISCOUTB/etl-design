from fastapi import APIRouter
from fastapi import HTTPException

from app.schemas.api import ApiResponse
from app.messaging.publishers import ValidationPublisher
from app.core.database_redis import redis_db

ENDPOINT = "schemas"
router = APIRouter()
publisher = ValidationPublisher()


@router.post("/upload/{import_name}")
async def upload_schema(
    import_name: str,
    schema: dict,
    raw: bool = False,
    new: bool = False,
) -> ApiResponse:
    """
    Upload a schema for validation.
    This endpoint allows users to upload a JSON schema for validation purposes.
    It checks if the schema is the same as the active schema in the database.
    If it is the same, no update is made. If it is different, the schema is saved
    as the active schema and added to the schemas_releases.
    """
    if not import_name:
        raise HTTPException(400, "import_name must be provided.")

    if not new and (
        cached_response := redis_db.get_tasks_by_import_name(
            import_name, endpoint=ENDPOINT
        )
    ):
        return cached_response

    try:
        task_id = publisher.publish_schema_update(
            schema=schema, import_name=import_name, raw=raw
        )

        response = ApiResponse(
            status="accepted",
            code=202,
            message="Schema upload request submitted successfully",
            data={"task_id": task_id, "import_name": import_name},
        )
    except Exception as e:
        task_id = None
        response = ApiResponse(
            status="error",
            code=500,
            message=f"Failed to upload schema: {str(e)}",
            data={"task_id": task_id, "import_name": import_name},
        )

    redis_db.set_task_id(task_id, response, endpoint=ENDPOINT)
    return response


@router.get("/status")
async def get_schema_task(
    task_id: str = "", import_name: str = ""
) -> list[ApiResponse] | ApiResponse:
    """
    Get the status of a schema upload task.
    This endpoint retrieves the status of a schema upload task by its ID.
    """
    if not task_id and not import_name:
        raise HTTPException(400, "Either task_id or import_name must be provided.")

    if import_name:
        tasks = redis_db.get_tasks_by_import_name(import_name, endpoint=ENDPOINT)
        return tasks

    cached_response = redis_db.get_task_id(task_id, endpoint=ENDPOINT)
    if not cached_response:
        raise HTTPException(404, f"Task with ID {task_id} not found.")

    return cached_response
