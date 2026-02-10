from typing import List

from fastapi import APIRouter, HTTPException
from proto_utils.database import dtypes

from src.api.deps import DatabaseClientDep
from src.core.constants import VALIDATION_TASK

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    database_client: DatabaseClientDep,
    task: str = VALIDATION_TASK,
) -> dtypes.ApiResponse:
    """Get the status of a long-running task by its ID."""
    cached_response = database_client.get_task_id(
        dtypes.GetTaskIdRequest(task_id=task_id, task=task)
    )

    if not cached_response["found"] or cached_response["value"] is None:
        raise HTTPException(404, f"Task with ID {task_id} not found.")

    return cached_response["value"]


@router.get("/")
async def list_tasks(
    database_client: DatabaseClientDep,
    import_name: str,
    task: str = VALIDATION_TASK,
) -> List[dtypes.ApiResponse]:
    """List all tasks associated with a specific import name."""
    response = database_client.get_tasks_by_import_name(
        dtypes.GetTasksByImportNameRequest(import_name=import_name, task=task)
    )
    if not response["tasks"]:
        raise HTTPException(404, f"No tasks found for import name {import_name}.")

    return response["tasks"]


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    database_client: DatabaseClientDep,
    task: str = VALIDATION_TASK,
) -> dtypes.ApiResponse:
    """Retry a failed task by its ID."""
    # TODO: Implement the logic to retry the task, e.g., by re-queuing it or resetting its status.
    pass
