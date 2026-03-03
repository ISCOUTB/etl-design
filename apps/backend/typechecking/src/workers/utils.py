from typing import Any, Dict, Optional

from proto_utils.database import dtypes

from src.core.database_client import DatabaseClient


def get_task_status(
    *,
    task_id: str,
    task: str,
    database_client: DatabaseClient,
) -> Optional[str]:
    """Get the current status of a task from the database.

    Args:
        task_id (str): The unique identifier of the task.
        task (str): The type of task (e.g., "validation", "insertion").
        database_client (DatabaseClient): The database client to use.

    Returns:
        Optional[str]: The current status of the task, or None if not found.
    """
    try:
        response = database_client.get_task_id(
            dtypes.GetTaskIdRequest(task_id=task_id, task=task)
        )

        if response["found"] and response["value"]:
            return response["value"]["status"]
    except Exception:
        pass

    return None


def update_task_status(
    *,
    task_id: str,
    field: str,
    value: Any,
    task: str,
    database_client: DatabaseClient,
    message: str = "",
    data: Optional[Dict[str, str]] = None,
    reset_data: bool = False,
) -> None:
    """Update the status of a task in the database.

    Args:
        task_id (str): The unique identifier of the task.
        field (str): The field to update (e.g., "status", "progress").
        value (Any): The new value for the specified field.
        task (str): The type of task (e.g., "schema_validation").
        database_client (DatabaseClient): The database client to use.
        message (str): An optional message to include with the update.
        data (Optional[Dict[str, str]]): Additional data to attach to the task.
        reset_data (bool): Whether to reset existing data for the task.

    Returns:
        None: This function does not return a value.
    """
    if data is None:
        data = {}

    database_client.update_task_id(
        dtypes.UpdateTaskIdRequest(
            task_id=task_id,
            field=field,
            value=value,
            task=task,
            message=message,
            data=data,
            reset_data=reset_data,
        )
    )
