from datetime import datetime
from typing import List, Dict, Tuple, Any

from jsonschema import validate, ValidationError, Draft7Validator

import pymongo.results
from app.core.database_mongo import mongo_connection


def compare_schemas(schema1: dict, schema2: dict) -> bool:
    """
    Compare two JSON schemas for equality.
    Returns True if they are equal, False otherwise.
    """
    return schema1 == schema2


def validate_data_chunk(data_chunk: List[Dict], schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a chunk of data against a JSON schema.

    Args:
        data_chunk (List[Dict]): A list of data items to validate.
        schema (Dict): The JSON schema to validate against.

    Returns:
        Tuple[bool, List[str]]: A tuple containing a boolean indicating if all items are valid,
                               and a list of validation error messages.
    """
    errors = []
    for i, item in enumerate(data_chunk):
        try:
            validate(instance=item, schema=schema)
        except ValidationError as e:
            errors.append(f"Item {i}: {e.message}")
        except Exception as e:
            errors.append(f"Item {i}: Unexpected error - {str(e)}")

    return len(errors) == 0, errors


def get_active_schema(import_name: str) -> Dict | None:
    """
    Get the active schema for a given import name.

    Args:
        import_name (str): The name of the import.

    Returns:
        Dict | None: The active schema if found, None otherwise.
    """
    schema_doc = mongo_connection.find_one({"import_name": import_name})
    if schema_doc and "active_schema" in schema_doc:
        return schema_doc["active_schema"]
    return None


def create_schema(raw: bool, kwargs) -> Dict:
    """
    Create a JSON schema from the provided keyword arguments.

    Args:
        raw (bool): Indicates if the schema is raw or not.
        kwargs: Key-value pairs representing the schema properties.

    Returns:
        Dict: The created JSON schema.

    Raises:
        SchemaError: If the raw schema is invalid.
    """
    if not raw:
        # TODO: Implement proper schema creation logic for non-raw schemas.
        return {
            "type": "object",
            "properties": kwargs,
            "required": list(kwargs.keys()),
            "additionalProperties": False,
        }

    Draft7Validator.check_schema(kwargs)
    return kwargs


def save_schema(schema: dict, import_name: str) -> Dict[str, Any] | None:
    """
    Save the schema to the MongoDB collection.
    If the schema is the same as the active schema, no update is needed.
    Otherwise, update the active schema and add it to the schemas_releases.

    Args:
        schema (dict): The JSON schema to save.
        import_name (str): The name of the import, used as a unique identifier.
    Returns:
        pymongo.results.InsertOneResult or pymongo.results.UpdateResult or None:
        The result of the insert or update operation.
    """
    schemas_releases = mongo_connection.find_one({"import_name": import_name})

    if mongo_connection.count_documents() == 0 or schemas_releases is None:
        result: pymongo.results.InsertOneResult = mongo_connection.insert_one(
            {
                "import_name": import_name,
                "created_at": datetime.now().isoformat(),
                "active_schema": schema.copy(),
                "schemas_releases": [],
            }
        )

        return {"status": "inserted", "acknowledged": result.acknowledged}

    if compare_schemas(schemas_releases["active_schema"], schema):
        print("Schema is the same, no update needed.")
        return None

    result: pymongo.results.UpdateResult = mongo_connection.update_one(
        {
            "import_name": import_name,
        },
        {
            "$set": {
                "active_schema": schema.copy(),
                "created_at": datetime.now().isoformat(),
            },
            "$push": {
                "schemas_releases": {
                    "schema": schema.copy(),
                }
            },
        },
    )
    return {"status": "Active Schema Updated", **result.raw_result}


def remove_schema(import_name: str) -> Dict[str, Any] | None:
    """
    Remove or revert a schema based on its import name.

    This function handles schema removal by either deleting the entire schema
    document if no releases exist, or reverting to the previous schema release
    by removing the most recent release and setting the active schema to the
    last available release.

    Args:
        import_name (str): The unique identifier for the schema to be removed.

    Returns:
        Dict[str, Any] | None: Returns None if the schema doesn't exist.
                              If no releases exist, returns the MongoDB delete result.
                              If releases exist, returns a dictionary containing
                              status information and the MongoDB update result.

    Note:
        - If the schema document doesn't exist, returns None
        - If no releases exist, the entire document is deleted
        - If releases exist, reverts to the previous schema by:
            * Setting active_schema to the last release's schema
            * Updating the created_at timestamp
            * Removing the most recent release from schemas_releases array
    """
    # Check if the import_name exists in the database
    schema_doc = mongo_connection.find_one({"import_name": import_name})
    if not schema_doc:
        return None

    releases = schema_doc.get("schemas_releases", [])

    # If there are no releases, delete the document
    if not releases:
        result: pymongo.results.DeleteResult = mongo_connection.delete_one(
            {"import_name": import_name}
        )
        return result

    # Remove the active schema and revert to the previous schema
    result: pymongo.results.UpdateResult = mongo_connection.update_one(
        {"import_name": import_name},
        {
            "$set": {
                "active_schema": releases[-1].get("schema", {}),
                "created_at": datetime.now().isoformat(),
            },
            "$pop": {"schemas_releases": 1},  # Remove the last schema release
        },
    )

    return {"status": "Active Schema Replaced with Last Release", **result.raw_result}
