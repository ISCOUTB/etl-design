# When a RabbitMQ Task is completed, it should notify the backend via an API endpoint.
# This module defines an API route for handling such notifications. When a task is completed
# the RabbitMQ worker can send a POST request to this endpoint with the task ID and status.
# The backend can notify the frontend about the task completion via WebHooks.

import json

from fastapi import APIRouter
from proto_utils.database import dtypes

from src import models, schemas
from src.api.deps import IdempotencyServiceDep
from src.utils import logger

router = APIRouter()


@router.post("/task-completed")
async def task_completed(
    idempotency_service: IdempotencyServiceDep,
    payload: schemas.TaskCompletionNotification,
) -> dtypes.ApiResponse:
    # TODO: Implement the logic to handle the task completion notification
    # For example, we could update the task status in the database and trigger a
    # WebHook to notify the frontend.

    logger.info(
        f"Received task completion notification: task_id={payload.task_id}, "
        f"status={payload.status}, message={payload.message}, idempotency_key={payload.idempotency_key}, "
        f"raw_data={payload.raw_data}"
    )

    # Load register from database
    task = idempotency_service.get_task_by_id(task_id=payload.task_id)
    if task is None:
        return dtypes.ApiResponse(
            code=404,
            status="task-not-found",
            message=f"No task found with ID {payload.task_id}",
            data={},
        )

    if task.status in [models.TaskStatus.COMPLETED, models.TaskStatus.FAILED]:
        return dtypes.ApiResponse(
            code=200,
            status="already-processed",
            message="Task already marked as completed",
            data={"task_id": payload.task_id, "status": task.status.value},
        )

    updated_status = (
        models.TaskStatus.COMPLETED
        if payload.status.lower() == "success"
        else models.TaskStatus.FAILED
    )

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

    parsed_raw_data = (
        dict(map(lambda item: (item[0], json.dumps(item[1])), payload.raw_data.items()))
        if payload.raw_data is not None
        else {}
    )

    return dtypes.ApiResponse(
        code=200,
        status="received-request",
        message="Task completion received",
        data={
            "task_id": payload.task_id,
            "status": payload.status,
            "message": payload.message,
            "idempotency_key": (
                payload.idempotency_key if payload.idempotency_key else ""
            ),
            "raw_data": json.dumps(parsed_raw_data),
        },
    )
