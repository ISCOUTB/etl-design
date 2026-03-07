from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

from proto_utils.database import dtypes

from src.core.database_mongo import MongoConnection
from src.services.mongo import MongoSchemasService


def test_compare_different_schemas() -> None:
    json_schema_1: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    json_schema_2: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
            "address": {"type": "string"},
        },
        "required": ["name", "email", "address"],
    }

    response = MongoSchemasService.compare_schemas(
        schema1=json_schema_1, schema2=json_schema_2
    )

    assert response is False


def test_compare_identical_schemas() -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    response = MongoSchemasService.compare_schemas(
        schema1=json_schema, schema2=json_schema.copy()
    )

    assert response is True


def test_count_all_documents(mongo_schemas_connection: MongoConnection) -> None:
    response = MongoSchemasService.count_all_documents(
        mongo_schemas_connection=mongo_schemas_connection
    )
    assert isinstance(response["amount"], int)
    assert response["amount"] >= 0


def test_insert_one_schema(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    response = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=f"import_name_test-{uuid4()}",
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "inserted"


def test_find_one_jsonschema(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=(datetime.now()).isoformat(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response = MongoSchemasService.find_one_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "found"
    assert response["extra"]["import_name"] == import_name
    assert MongoSchemasService.compare_schemas(response["schema"], json_schema) is True


def test_find_one_jsonschema_not_found(
    mongo_schemas_connection: MongoConnection,
) -> None:
    response = MongoSchemasService.find_one_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=f"non_existent-{uuid4()}"),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "not_found"
    assert response["schema"] is None


def test_insert_one_schema_duplicate(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    response1 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response2 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response1["status"] == "inserted"
    assert response2["status"] == "no_change"


def test_insert_one_schema_update(mongo_schemas_connection: MongoConnection) -> None:
    json_schema_v1: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    json_schema_v2: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
            "address": {"type": "string"},
        },
        "required": ["name", "email", "address"],
    }

    import_name = f"import_name_test-{uuid4()}"

    response1 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now().isoformat(),
            active_schema=json_schema_v1,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response2 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now().isoformat(),
            active_schema=json_schema_v2,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response1["status"] == "inserted"
    assert response2["status"] == "updated"

    # Verify schema releases
    find_response = MongoSchemasService.get_raw_schemas(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert find_response is not None
    assert len(find_response["schemas_releases"]) == 1
    assert (
        MongoSchemasService.compare_schemas(
            find_response["schemas_releases"][0]["schema"], json_schema_v1
        )
        is True
    )


def test_update_one_schema(mongo_schemas_connection: MongoConnection) -> None:
    json_schema_v1: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    json_schema_v2: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
            "address": {"type": "string"},
        },
        "required": ["name", "email", "address"],
    }

    import_name = f"import_name_test-{uuid4()}"

    response1 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema_v1,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response2 = MongoSchemasService.update_one_schema(
        request=dtypes.MongoUpdateOneJsonSchemaRequest(
            import_name=import_name,
            schema=json_schema_v2,
            created_at=datetime.now(),
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response1["status"] == "inserted"
    assert response2["status"] == "updated"


def test_update_one_schema_not_found(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    response = MongoSchemasService.update_one_schema(
        request=dtypes.MongoUpdateOneJsonSchemaRequest(
            import_name=f"non_existent-{uuid4()}",
            schema=json_schema,
            created_at=datetime.now(),
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "error"


def test_update_one_schema_no_change(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    response1 = MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response2 = MongoSchemasService.update_one_schema(
        request=dtypes.MongoUpdateOneJsonSchemaRequest(
            import_name=import_name,
            schema=json_schema,
            created_at=datetime.now(),
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response1["status"] == "inserted"
    assert response2["status"] == "no_change"


def test_delete_one_schema_with_no_releases(
    mongo_schemas_connection: MongoConnection,
) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response = MongoSchemasService.delete_one_schema(
        request=dtypes.MongoDeleteOneJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "deleted"

    # Verify deletion
    find_response = MongoSchemasService.find_one_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert find_response["status"] == "not_found"


def test_delete_one_schema_with_releases(
    mongo_schemas_connection: MongoConnection,
) -> None:
    json_schema_v1: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    json_schema_v2: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
            "address": {"type": "string"},
        },
        "required": ["name", "email", "address"],
    }

    import_name = f"import_name_test-{uuid4()}"

    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now().isoformat(),
            active_schema=json_schema_v1,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=(datetime.now() + timedelta(minutes=10)).isoformat(),
            active_schema=json_schema_v2,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response = MongoSchemasService.delete_one_schema(
        request=dtypes.MongoDeleteOneJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "reverted"

    # Verify reversion
    find_response = MongoSchemasService.find_one_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert find_response["status"] == "found"
    assert (
        MongoSchemasService.compare_schemas(find_response["schema"], json_schema_v1)
        is True
    )


def test_delete_one_schema_not_found(mongo_schemas_connection: MongoConnection) -> None:
    response = MongoSchemasService.delete_one_schema(
        request=dtypes.MongoDeleteOneJsonSchemaRequest(
            import_name=f"non_existent-{uuid4()}"
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "error"


def test_delete_import_name(mongo_schemas_connection: MongoConnection) -> None:
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    response = MongoSchemasService.delete_import_name(
        request=dtypes.MongoDeleteImportNameRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "deleted"

    # Verify deletion
    find_response = MongoSchemasService.find_one_jsonschema(
        dtypes.MongoFindJsonSchemaRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert find_response["status"] == "not_found"


def test_delete_import_name_not_found(
    mongo_schemas_connection: MongoConnection,
) -> None:
    response = MongoSchemasService.delete_import_name(
        request=dtypes.MongoDeleteImportNameRequest(
            import_name=f"non_existent-{uuid4()}"
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["status"] == "error"


def test_ping(mongo_schemas_connection: MongoConnection) -> None:
    response = MongoSchemasService.ping(
        mongo_schemas_connection=mongo_schemas_connection
    )
    assert response["pong"] is True


def test_get_raw_schemas_success(mongo_schemas_connection: MongoConnection) -> None:
    """Test getting raw schemas successfully."""
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    # Insert a schema first
    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Get raw schemas
    response = MongoSchemasService.get_raw_schemas(
        request=dtypes.MongoGetRawSchemasRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Assert the response
    assert response is not None
    assert response["import_name"] == import_name
    assert response["id"] is not None
    assert response["created_at"] is not None
    assert "active_schema" in response
    assert "schemas_releases" in response
    assert response["active_schema"] == json_schema
    assert isinstance(response["schemas_releases"], list)


def test_get_raw_schemas_with_releases(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting raw schemas with multiple releases."""
    json_schema_v1: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }

    json_schema_v2: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string", "format": "email"},
        },
        "required": ["name", "email"],
    }

    import_name = f"import_name_test-{uuid4()}"

    # Insert first version
    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema_v1,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Insert second version (will create a release)
    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now() + timedelta(minutes=5),
            active_schema=json_schema_v2,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Get raw schemas
    response = MongoSchemasService.get_raw_schemas(
        request=dtypes.MongoGetRawSchemasRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Assert the response
    assert response is not None
    assert response["import_name"] == import_name
    assert response["active_schema"] == json_schema_v2
    assert len(response["schemas_releases"]) == 1
    assert response["schemas_releases"][0]["schema"] == json_schema_v1
    assert "created_at" in response["schemas_releases"][0]


def test_get_raw_schemas_not_found(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting raw schemas for non-existent import name."""
    import_name = f"non_existent-{uuid4()}"

    # Try to get raw schemas for non-existent import name
    response = MongoSchemasService.get_raw_schemas(
        request=dtypes.MongoGetRawSchemasRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Assert the response is None for not found
    assert response is None


def test_get_raw_schemas_empty_releases(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting raw schemas with no releases."""
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }

    import_name = f"import_name_test-{uuid4()}"

    # Insert a schema without any previous releases
    MongoSchemasService.insert_one_schema(
        request=dtypes.MongoInsertOneSchemaRequest(
            import_name=import_name,
            created_at=datetime.now(),
            active_schema=json_schema,
            schemas_releases=[],
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Get raw schemas
    response = MongoSchemasService.get_raw_schemas(
        request=dtypes.MongoGetRawSchemasRequest(import_name=import_name),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    # Assert the response
    assert response is not None
    assert response["import_name"] == import_name
    assert response["active_schema"] == json_schema
    assert len(response["schemas_releases"]) == 0


def test_get_schemas_by_import_regex_success(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting schemas by import_name regex returns matching documents."""
    json_schema: dtypes.JsonSchema = {
        "schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
        "required": ["name"],
    }

    pattern_seed = f"regex_match_{uuid4()}"
    matching_import_names = [
        f"{pattern_seed}_v1",
        f"{pattern_seed}_v2",
    ]
    non_matching_import_name = f"other_import_{uuid4()}"

    for import_name in [*matching_import_names, non_matching_import_name]:
        MongoSchemasService.insert_one_schema(
            request=dtypes.MongoInsertOneSchemaRequest(
                import_name=import_name,
                created_at=datetime.now(),
                active_schema=json_schema,
                schemas_releases=[],
            ),
            mongo_schemas_connection=mongo_schemas_connection,
        )

    response = MongoSchemasService.get_schemas_by_import_regex(
        request=dtypes.MongoGetSchemasByImportRegexRequest(import_name=pattern_seed),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    returned_import_names = {schema["import_name"] for schema in response["schemas"]}
    assert returned_import_names == set(matching_import_names)
    assert len(response["schemas"]) == 2


def test_get_schemas_by_import_regex_no_matches(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting schemas by import_name regex with no matches."""
    response = MongoSchemasService.get_schemas_by_import_regex(
        request=dtypes.MongoGetSchemasByImportRegexRequest(
            import_name=f"non_existent_pattern_{uuid4()}"
        ),
        mongo_schemas_connection=mongo_schemas_connection,
    )

    assert response["schemas"] == []


def test_get_schemas_by_import_regex_on_error_returns_empty_list(
    mongo_schemas_connection: MongoConnection,
) -> None:
    """Test getting schemas by import_name regex returns empty list on DB errors."""
    with patch.object(
        mongo_schemas_connection,
        "find",
        side_effect=Exception("Database error"),
    ):
        response = MongoSchemasService.get_schemas_by_import_regex(
            request=dtypes.MongoGetSchemasByImportRegexRequest(import_name="any"),
            mongo_schemas_connection=mongo_schemas_connection,
        )

    assert response["schemas"] == []
