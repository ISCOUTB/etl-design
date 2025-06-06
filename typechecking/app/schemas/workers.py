from typing import TypedDict, Literal, Dict, Any
from pymongo.results import UpdateResult, InsertOneResult
from app.schemas.controllers import ValidationSummary


class DataValidated(TypedDict):
    """
    TypedDict for data validation results.
    """
    task_id: str
    status: Literal["completed", "failed"]
    results: ValidationSummary


class SchemaUpdated(TypedDict):
    """
    TypedDict for schema update results.
    """
    task_id: str
    status: Literal["completed", "failed"]
    schema: Dict[str, Any]  # The updated JSON schema
    import_name: str
    result: UpdateResult | InsertOneResult | None
