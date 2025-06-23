"""Controller Schemas Module.

This module defines TypedDict schemas used by controller layer components
for validation results and summary information. These schemas provide
structured data formats for validation operations and result reporting.

The schemas support the validation workflow from individual validation
results to comprehensive summaries with detailed statistics and error
information.
"""
from typing import TypedDict, Optional


class ValidationResults(TypedDict):
    """Detailed validation results schema.
    
    Contains comprehensive validation information including validity status,
    item counts, error details, and summary messages. Used to represent
    the complete results of a file validation operation.
    
    Attributes:
        is_valid: Overall validation status - True if all items are valid.
        total_items: Total number of items/records processed in the file.
        valid_items: Count of items that passed validation rules.
        invalid_items: Count of items that failed validation rules.
        errors: List of error messages describing validation failures.
        message: Human-readable summary message of the validation results.
        
    Example:
        >>> results: ValidationResults = {
        ...     "is_valid": False,
        ...     "total_items": 100,
        ...     "valid_items": 95,
        ...     "invalid_items": 5,
        ...     "errors": ["Row 10: Invalid email format", "Row 25: Missing required field"],
        ...     "message": "Validation completed with 5 errors"
        ... }
    """
    is_valid: bool
    total_items: int
    valid_items: int
    invalid_items: int
    errors: list[str]
    message: str


class ValidationResult(TypedDict):
    """Validation operation result wrapper.
    
    Wraps validation results with success status and error information.
    Used by controllers to return standardized validation responses
    with proper error handling.
    
    Attributes:
        success: Boolean indicating if the validation operation completed successfully.
        error: Error message if the validation operation failed, None if successful.
        validation_results: Detailed validation results, None if operation failed.
        
    Example:
        >>> result: ValidationResult = {
        ...     "success": True,
        ...     "error": None,
        ...     "validation_results": {
        ...         "is_valid": True,
        ...         "total_items": 50,
        ...         "valid_items": 50,
        ...         "invalid_items": 0,
        ...         "errors": [],
        ...         "message": "All items validated successfully"
        ...     }
        ... }
    """
    success: bool
    error: Optional[str]
    validation_results: Optional[ValidationResults]


class SummaryDetails(TypedDict):
    """Detailed summary information for validation results.
    
    Provides comprehensive statistics and metadata about a validation
    operation including item counts, file information, and timing data.
    Used within validation summaries for detailed reporting.
    
    Attributes:
        total_items: Total number of items processed.
        valid_items: Count of successfully validated items.
        invalid_items: Count of items that failed validation.
        error_count: Total number of validation errors encountered.
        file_name: Name of the validated file, None if not available.
        validated_at: ISO timestamp of when validation was performed, None if not recorded.
        
    Example:
        >>> details: SummaryDetails = {
        ...     "total_items": 1000,
        ...     "valid_items": 950,
        ...     "invalid_items": 50,
        ...     "error_count": 75,
        ...     "file_name": "customer_data.csv",
        ...     "validated_at": "2024-01-15T10:30:00Z"
        ... }
    """
    total_items: int
    valid_items: int
    invalid_items: int
    error_count: int
    file_name: str | None
    validated_at: str | None


class ValidationSummary(TypedDict):
    """High-level validation summary schema.
    
    Provides a concise summary of validation results with status,
    summary message, and optional detailed information. Used for
    API responses and result reporting.
    
    Attributes:
        status: Overall validation status ('valid', 'invalid', 'error', etc.).
        summary: Brief human-readable summary of the validation results.
        details: Optional detailed summary information, None for simple summaries.
        
    Example:
        >>> summary: ValidationSummary = {
        ...     "status": "partially_valid",
        ...     "summary": "950 of 1000 records validated successfully",
        ...     "details": {
        ...         "total_items": 1000,
        ...         "valid_items": 950,
        ...         "invalid_items": 50,
        ...         "error_count": 75,
        ...         "file_name": "data.csv",
        ...         "validated_at": "2024-01-15T10:30:00Z"
        ...     }
        ... }
    """
    status: str
    summary: str
    details: Optional[SummaryDetails]
