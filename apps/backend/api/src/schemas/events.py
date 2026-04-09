from typing import Any, Dict, Optional

from pydantic import BaseModel


class TaskCompletionNotification(BaseModel):
    task_id: str
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    # This model can be extended with additional fields as needed, such as timestamps,
    # user information, or any other relevant metadata related to the task completion event.
