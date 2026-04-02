from typing import List

from fastapi import APIRouter
from proto_utils.database import dtypes

from src.api.deps import CurrentUser, DatabaseClientDep, IdempotencyServiceDep
from src.core.constants import VALIDATION_TASK
from src.exceptions import ForbiddenException, TaskNotFoundException
from src.models import Project
from src.services.permissions import Action, ModelKeys, PermissionService

router = APIRouter()


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    idempotency_service: IdempotencyServiceDep,
    task: str = VALIDATION_TASK,
) -> dtypes.ApiResponse:
    """Get the status of a long-running task by its ID."""
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.view,
        model_key=ModelKeys.task,
    )
    if not has_permission:
        raise ForbiddenException()

    cached_response = await database_client.get_task_id_async(
        dtypes.GetTaskIdRequest(task_id=task_id, task=task)
    )
    if not cached_response["found"] or cached_response["value"] is None:
        # If not found in redis/mongo, search in the main database (PostgreSQL)
        # as a fallback
        task = idempotency_service.get_task_by_id(task_id=task_id)
        if task is None:
            raise TaskNotFoundException()

        return dtypes.ApiResponse(
            code=200,
            status=task.status.value,
            message="Task found in main database",
            data={"task_id": task_id, "status": task.status.value},
        )

    return cached_response["value"]


@router.get("/project/{project_id}")
async def list_tasks(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_id: str,
    table_name: str,
    task: str = VALIDATION_TASK,
) -> List[dtypes.ApiResponse]:
    """List all tasks associated with a specific import name."""
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.search,
        model_key=ModelKeys.task,
        model=Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    response = await database_client.get_tasks_by_import_name_async(
        dtypes.GetTasksByImportNameRequest(
            import_name=f"{project_id}__{table_name}", task=task
        )
    )

    tasks = response.get("tasks") or []

    return tasks
