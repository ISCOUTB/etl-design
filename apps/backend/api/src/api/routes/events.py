# When a RabbitMQ Task is completed, it should notify the backend via an API endpoint.
# This module defines an API route for handling such notifications. When a task is completed
# the RabbitMQ worker can send a POST request to this endpoint with the task ID and status.
# The backend can notify the frontend about the task completion via WebHooks.

from typing import Annotated

from fastapi import APIRouter, Body
from proto_utils.database import dtypes

router = APIRouter()


@router.post("/task-completed")
async def task_completed(
    task_id: Annotated[str, Body()],
    status: Annotated[str, Body()],
    message: Annotated[str, Body()],
) -> dtypes.ApiResponse:
    # TODO: Implement the logic to handle the task completion notification
    # For example, we could update the task status in the database and trigger a WebHook to notify the frontend.
    pass
