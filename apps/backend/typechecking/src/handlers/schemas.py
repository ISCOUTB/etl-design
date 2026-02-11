from proto_utils.database import dtypes

from src.core.database_client import DatabaseClient


def get_active_schema(
    import_name: str, database_client: DatabaseClient
) -> dtypes.JsonSchema | None:
    """
    Get the active schema for a given import name.

    Args:
        import_name (str): The name of the import.
        database_client (DatabaseClient): The database client to use for fetching the schema.

    Returns:
        Dict | None: The active schema if found, None otherwise.
    """
    schema_doc = database_client.mongo_find_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name)
    )

    return schema_doc["schema"] if schema_doc["status"] == "found" else None
