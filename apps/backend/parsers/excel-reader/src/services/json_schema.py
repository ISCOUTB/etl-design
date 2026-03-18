from typing import Any, Dict, Iterable, Tuple

from proto_utils.generated.parsers import ddl_generator_pb2, dtypes_pb2

from src import schemas


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)

    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _resolve_json_type(type_value: str | list[str] | None) -> Tuple[str, bool]:
    if isinstance(type_value, list):
        non_null_types = [item for item in type_value if item != "null"]
        if not non_null_types:
            return "string", True
        return non_null_types[0], "null" in type_value

    if isinstance(type_value, str):
        return type_value, False

    return "string", False


def _map_schema_type_to_sql(
    json_type: str, property_schema: Dict[str, Any]
) -> Tuple[str, int]:
    if json_type == "integer":
        return "INTEGER", dtypes_pb2.AstType.AST_NUMBER

    if json_type == "number":
        return "DOUBLE PRECISION", dtypes_pb2.AstType.AST_NUMBER

    if json_type == "boolean":
        return "BOOLEAN", dtypes_pb2.AstType.AST_LOGICAL

    if json_type == "string":
        string_format = property_schema.get("format")
        if string_format == "date-time":
            return "TIMESTAMP", dtypes_pb2.AstType.AST_TEXT
        if string_format == "date":
            return "DATE", dtypes_pb2.AstType.AST_TEXT
        if string_format == "time":
            return "TIME", dtypes_pb2.AstType.AST_TEXT

        max_length = property_schema.get("maxLength")
        if isinstance(max_length, int) and max_length > 0:
            return f"VARCHAR({max_length})", dtypes_pb2.AstType.AST_TEXT

        return "TEXT", dtypes_pb2.AstType.AST_TEXT

    return "JSONB", dtypes_pb2.AstType.AST_TEXT


def _build_extra_constraints(
    *,
    property_name: str,
    property_schema: Dict[str, Any],
    required_properties: Iterable[str],
    allows_null: bool,
) -> str:
    constraints: list[str] = []

    if property_name in required_properties and not allows_null:
        constraints.append("NOT NULL")

    if property_schema.get("unique") is True:
        constraints.append("UNIQUE")

    if "default" in property_schema:
        constraints.append(
            f"DEFAULT {_sql_literal(property_schema['default'])}"
        )

    return " ".join(constraints)


def _normalize_primary_keys(primary_keys: list[str] | None) -> set[str]:
    if primary_keys is None:
        return set()

    normalized_keys: set[str] = set()
    for key in primary_keys:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("'primary_keys' values must be non-empty strings")
        normalized_keys.add(key.strip())

    return normalized_keys


def _append_constraint(extra: str, constraint: str) -> str:
    normalized_extra = extra.strip()
    if not normalized_extra:
        return constraint

    if constraint.lower() in normalized_extra.lower():
        return normalized_extra

    return f"{normalized_extra} {constraint}".strip()


def json_schema_to_sql_builder_payload(
    schema: Dict[str, Any],
    primary_keys: list[str] | None = None,
) -> tuple[Dict[str, ddl_generator_pb2.DDLResponse], schemas.JSONSchemaDTypes]:
    if not isinstance(schema, dict):
        raise ValueError("'jsonschema' must be a JSON object")

    schema_type = schema.get("type", "object")
    if schema_type != "object":
        raise ValueError(
            "Only JSON schemas with root type 'object' are supported"
        )

    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ValueError(
            "JSON schema must define a non-empty 'properties' object"
        )

    required_properties = schema.get("required", [])
    if not isinstance(required_properties, list):
        raise ValueError("'required' must be an array of property names")

    normalized_primary_keys = _normalize_primary_keys(primary_keys)
    for primary_key in normalized_primary_keys:
        if primary_key not in properties:
            raise ValueError(
                f"Primary key column '{primary_key}' must exist in 'properties'"
            )

    cols: Dict[str, ddl_generator_pb2.DDLResponse] = {}
    dtypes: schemas.JSONSchemaDTypes = {}

    for property_name, property_schema in properties.items():
        if not isinstance(property_name, str) or not property_name.strip():
            raise ValueError("Property names must be non-empty strings")

        if not isinstance(property_schema, dict):
            raise ValueError(
                f"Invalid schema for property '{property_name}': expected an object"
            )

        json_type, allows_null = _resolve_json_type(property_schema.get("type"))
        sql_type, ast_type = _map_schema_type_to_sql(json_type, property_schema)

        extra = _build_extra_constraints(
            property_name=property_name,
            property_schema=property_schema,
            required_properties=required_properties,
            allows_null=allows_null,
        )

        if property_name in normalized_primary_keys:
            extra = _append_constraint(extra, "PRIMARY KEY")

        dtypes[property_name] = {
            "type": sql_type,
            "extra": extra,
        }

        if ast_type == dtypes_pb2.AstType.AST_NUMBER:
            cols[property_name] = ddl_generator_pb2.DDLResponse(
                type=ast_type,
                sql="0",
                number_value=0,
            )
            continue

        if ast_type == dtypes_pb2.AstType.AST_LOGICAL:
            cols[property_name] = ddl_generator_pb2.DDLResponse(
                type=ast_type,
                sql="FALSE",
                logical_value=False,
            )
            continue

        cols[property_name] = ddl_generator_pb2.DDLResponse(
            type=ast_type,
            sql="''",
            text_value="",
        )

    return cols, dtypes
