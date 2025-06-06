from typing import TypedDict, Optional


class ValidationResults(TypedDict):
    is_valid: bool
    total_items: int
    valid_items: int
    invalid_items: int
    errors: list[str]
    message: str


class ValidationResult(TypedDict):
    success: bool
    error: Optional[str]
    validation_results: Optional[ValidationResults]


class SummaryDetails(TypedDict):
    total_items: int
    valid_items: int
    invalid_items: int
    error_count: int
    file_name: str | None
    validated_at: str | None


class ValidationSummary(TypedDict):
    status: str
    summary: str
    details: Optional[SummaryDetails]
