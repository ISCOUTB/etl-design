from typing import List

from fastapi import APIRouter
from proto_utils.database import dtypes

from src.api.deps import CurrentUser, DatabaseClientDep
from src.core.constants import VALIDATION_TASK
from src.exceptions import ForbiddenException, TaskNotFoundException
from src.models import Project
from src.services.permissions import Action, ModelKeys, PermissionService

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
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

    cached_response = database_client.get_task_id(
        dtypes.GetTaskIdRequest(task_id=task_id, task=task)
    )

    if not cached_response["found"] or cached_response["value"] is None:
        raise TaskNotFoundException()

    return cached_response["value"]


@router.get("/{project_id}")
async def list_tasks(
    current_user: CurrentUser,
    database_client: DatabaseClientDep,
    project_id: str,
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

    response = database_client.get_tasks_by_import_name(
        dtypes.GetTasksByImportNameRequest(import_name=project_id, task=task)
    )
    if not response["tasks"]:
        raise TaskNotFoundException()

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
