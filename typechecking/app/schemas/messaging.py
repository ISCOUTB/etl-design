from typing import TypedDict


class ValidationMessage(TypedDict):
    """
    Represents a request message for validation.
    """
    id: str
    timestamp: str
    file_data: str  # Hex-encoded file data
    import_name: str
    metadata: dict  # Additional metadata for the request
    priority: int  # Priority of the request


class SchemaMessage(TypedDict):
    """
    Represents a message for schema updates.
    """
    id: str
    timestamp: str
    schema: dict  # The JSON schema to be updated
    import_name: str  # The name of the import associated with the schema
