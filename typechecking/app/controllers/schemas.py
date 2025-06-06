from datetime import datetime
from typing import List, Dict, Tuple

from jsonschema import validate, ValidationError

import pymongo.results
from app.core.database import mongo_connection


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


def create_schema(**kwargs) -> Dict:
    """
    Create a JSON schema from the provided keyword arguments.

    Args:
        **kwargs: Key-value pairs representing the schema properties.

    Returns:
        Dict: The created JSON schema.
    """
    return {
        "type": "object",
        "properties": kwargs,
        "required": list(kwargs.keys()),
        "additionalProperties": False,
    }


def save_schema(
    schema: dict, import_name: str
) -> pymongo.results.InsertOneResult | pymongo.results.UpdateResult | None:
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
        return mongo_connection.insert_one(
            {
                "import_name": import_name,
                "created_at": datetime.now().isoformat(),
                "active_schema": schema.copy(),
                "schemas_releases": [],
            }
        )

    if compare_schemas(schemas_releases["active_schema"], schema):
        print("Schema is the same, no update needed.")
        return None

    return mongo_connection.update_one(
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
