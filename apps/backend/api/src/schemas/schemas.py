from typing import Any, Dict, List, TypedDict

from proto_utils.database import dtypes
from pydantic import BaseModel

JsonSchemaRequest = TypedDict(
    "JsonSchemaRequest",
    {
        "$schema": str,
        "properties": Dict[str, Any],
        "required": List[str],
        "type": str,
    },
)


class CreateTableResponse(BaseModel):
    """
    Base model for create responses.

    Attributes:
        message (str): A message indicating the result of the operation.
        sql_per_sheet (Dict[str, str]): A dictionary mapping sheet names to their corresponding SQL
            statements.
        schema_saved (Dict[str, dtypes.MongoInsertOneSchemaResponse]): A dictionary mapping sheet
            names to their corresponding schema save responses.
    """

    message: str
    sql_per_sheet: Dict[str, str]
    schema_saved: Dict[str, dtypes.MongoInsertOneSchemaResponse]


class MongoSchemasResponseSchemaRelease(TypedDict):
    """Inner structure for individual schema releases in the MongoGetRawSchemasResponse.

    Attributes:
        created_at (str): ISO timestamp when this schema version was created
        schema (JsonSchemaRequest): The JSON schema definition for this version
    """

    created_at: str
    schema: JsonSchemaRequest


class MongoSchemasResponse(BaseModel):
    """Response message containing all raw schema documents matching the import name.

    Attributes:
        id (str): Unique identifier of the document in MongoDB
        import_name (str): The unique identifier of the import name associated with these schemas
        created_at (str): ISO timestamp when the document was created
        active_schema (JsonSchemaRequest): The currently active/latest version of the schema
        schemas_releases (List[MongoSchemasResponseSchemaRelease]): Historical versions of the schema for versioning
    """

    id: str
    import_name: str
    created_at: str
    active_schema: JsonSchemaRequest
    schemas_releases: List[MongoSchemasResponseSchemaRelease]


class MongoGetSchemasByImportResponse(TypedDict):
    """Response structure for MongoGetSchemasByImportRegex gRPC method.

    Attributes:
        schemas (List[MongoSchemasResponse]): A list of schema documents matching the import name regex.
    """

    schemas: List[MongoSchemasResponse]
