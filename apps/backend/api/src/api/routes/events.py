# When a RabbitMQ Task is completed, it should notify the backend via an API endpoint.
# This module defines an API route for handling such notifications. When a task is completed
# the RabbitMQ worker can send a POST request to this endpoint with the task ID and status.
# The backend can notify the frontend about the task completion via WebHooks.

import json
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Body
from proto_utils.database import dtypes

from src import models
from src.api.deps import IdempotencyServiceDep

router = APIRouter()


@router.post("/task-completed")
async def task_completed(
    idempotency_service: IdempotencyServiceDep,
    task_id: Annotated[str, Body()],
    idempotency_key: Annotated[Optional[str], Body()],
    status: Annotated[str, Body()],
    message: Annotated[str, Body()],
    raw_data: Annotated[Optional[Dict[str, Any]], Body()] = None,
) -> dtypes.ApiResponse:
    # TODO: Implement the logic to handle the task completion notification
    # For example, we could update the task status in the database and trigger a
    # WebHook to notify the frontend.

    print(
        f"Received task completion notification: task_id={task_id}, "
        f"status={status}, message={message}, idempotency_key={idempotency_key}, "
        f"raw_data={raw_data}"
    )

    # Load register from database
    task = idempotency_service.get_task_by_id(task_id=task_id)
    if task is None:
        return dtypes.ApiResponse(
            code=404,
            status="task-not-found",
            message=f"No task found with ID {task_id}",
            data={},
        )

    if task.status in [models.TaskStatus.COMPLETED, models.TaskStatus.FAILED]:
        return dtypes.ApiResponse(
            code=200,
            status="already-processed",
            message="Task already marked as completed",
            data={"task_id": task_id, "status": task.status.value},
        )

    updated_status = models.TaskStatus.COMPLETED if status.lower() == "success" else models.TaskStatus.FAILED

    try:
        # Update task status in the database
        idempotency_service.update_task_status(status=updated_status, db_obj=task)
    except Exception as e:
        return dtypes.ApiResponse(
            code=500,
            status="update-failed",
            message=f"Failed to update task status: {str(e)}",
            data={},
        )

    return dtypes.ApiResponse(
        code=200,
        status="received-request",
        message="Task completion received",
        data={
            "task_id": task_id,
            "status": status,
            "message": message,
            "raw_data": json.dumps(raw_data),
        },
    )
