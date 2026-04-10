from typing import List, Optional

from fastapi import APIRouter
from proto_utils.database import dtypes

from src.api.deps import CurrentUser, DatabaseClientDep, IdempotencyServiceDep
from src.core.constants import INSERTION_TASK, VALIDATION_TASK
from src.core.domain import get_import_name
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
    task: Optional[str] = None,
) -> dtypes.ApiResponse:
    """Get the status of a long-running task by its ID."""
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.view,
        model_key=ModelKeys.task,
    )
    if not has_permission:
        raise ForbiddenException()

    if task is None:
        # If task type is not specified, check for both validation and insertion tasks
        cached_response = await database_client.get_task_id_async(
            dtypes.GetTaskIdRequest(task_id=task_id, task=VALIDATION_TASK)
        )
        if not cached_response["found"] or cached_response["value"] is None:
            cached_response = await database_client.get_task_id_async(
                dtypes.GetTaskIdRequest(task_id=task_id, task=INSERTION_TASK)
            )
    else:
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
    task: Optional[str] = None,
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

    import_name = get_import_name(project_id=project_id, table_name=table_name)
    if task is None:
        response_validation_tasks = database_client.get_tasks_by_import_name_async(
            dtypes.GetTasksByImportNameRequest(
                import_name=import_name, task=VALIDATION_TASK
            )
        )

        response_insertion_tasks = database_client.get_tasks_by_import_name_async(
            dtypes.GetTasksByImportNameRequest(
                import_name=import_name, task=INSERTION_TASK
            )
        )

        response_validation_tasks, response_insertion_tasks = (
            await response_validation_tasks,
            await response_insertion_tasks,
        )

        validation_tasks = response_validation_tasks.get("tasks") or []
        insertion_tasks = response_insertion_tasks.get("tasks") or []
        tasks = validation_tasks + insertion_tasks
    else:
        response = await database_client.get_tasks_by_import_name_async(
            dtypes.GetTasksByImportNameRequest(import_name=import_name, task=task)
        )
        tasks = response.get("tasks") or []

    return tasks
