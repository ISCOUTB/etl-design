"""Worker Schemas Module.

This module defines TypedDict schemas for worker result messages
in the typechecking system. These schemas standardize the format
of results returned by validation and schema workers after processing
their respective message types.

The schemas ensure consistent result structure for downstream consumers
and provide proper typing for worker result handling and storage.
"""

from typing import Dict, Literal, NotRequired, Optional, TypedDict

from src.schemas.handlers import SummaryStatus, ValidationSummary


class DataValidated(TypedDict):
    """Data validation result schema.

    Represents the result of a file validation operation performed
    by validation workers. Contains the task identifier, completion
    status, and detailed validation results for further processing.

    Used by validation workers to report results back to the system
    and by result consumers to process validation outcomes.

    Attributes:
        task_id (str): Unique identifier linking back to the original validation request.
        status (SummaryStatus): Completion status - 'success' for successful validation,
            'failed' for validation processing errors.
        results (ValidationSummary): Detailed validation summary including statistics, status,
            and validation details from the ValidationSummary schema.

    Example:
        >>> result: DataValidated = {
        ...     "task_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "status": "success",
        ...     "results": {
        ...         "status": "success",
        ...         "summary": "All 100 records validated successfully",
        ...         "details": {
        ...             "total_items": 100,
        ...             "valid_items": 100,
        ...             "invalid_items": 0,
        ...             "error_count": 0,
        ...             "file_name": "data.csv",
        ...             "validated_at": "2024-01-15T10:30:00Z"
        ...         }
        ...     }
        ... }
    """

    task_id: str
    project_id: str
    import_name: str
    status: SummaryStatus
    results: ValidationSummary
    error: NotRequired[str]
    traceparent: Optional[str]
    tracestate: Optional[str]
    baggage: Optional[str]


class InsertionResult(TypedDict):
    task_id: str
    project_id: str
    import_name: str
    results: Dict[str, str]
    status: Literal["success", "failed"]
    error: NotRequired[str]
    traceparent: Optional[str]
    tracestate: Optional[str]
    baggage: Optional[str]


class ResultsMessage(TypedDict):
    task_id: str
    project_id: str
    import_name: str
    results: Dict[str, str]
    status: str
    error: NotRequired[str]
    traceparent: Optional[str]
    tracestate: Optional[str]
    baggage: Optional[str]
