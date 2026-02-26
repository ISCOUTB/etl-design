from typing import Dict, Literal, Optional, TypedDict

from messaging_utils.schemas.common import Metadata

ValidationTasks = Literal["sample_validation", "unknown"]


class ValidationMessage(TypedDict):
    id: str
    task: ValidationTasks
    file_data: str
    project_id: str
    table_name: str
    metadata: Metadata
    date: str
    extra: Dict[str, str]
    insert: bool
    insert_overwrite: Optional[bool]
    insert_db_uri: Optional[str]
    idempotency_key: Optional[str]
