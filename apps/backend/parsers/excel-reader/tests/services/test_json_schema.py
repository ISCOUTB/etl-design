import sys
from pathlib import Path

from fastapi.testclient import TestClient
from proto_utils.generated.parsers import dtypes_pb2

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.server_rest import app
from src.services.json_schema import json_schema_to_sql_builder_payload
from src.utils.deps import get_sql_builder_stub


class _FakeSQLBuilderStub:
    pass


def test_json_schema_to_sql_builder_payload_maps_types_and_constraints():
    cols, dtypes = json_schema_to_sql_builder_payload(
        {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {
                    "type": "string",
                    "maxLength": 120,
                    "default": "anonymous",
                },
                "active": {"type": "boolean", "default": True},
            },
        }
    )

    assert dtypes["id"] == {"type": "INTEGER", "extra": "NOT NULL"}
    assert dtypes["name"] == {
        "type": "VARCHAR(120)",
        "extra": "NOT NULL DEFAULT 'anonymous'",
    }
    assert dtypes["active"] == {"type": "BOOLEAN", "extra": "DEFAULT TRUE"}

    assert cols["id"].type == dtypes_pb2.AstType.AST_NUMBER
    assert cols["name"].type == dtypes_pb2.AstType.AST_TEXT
    assert cols["active"].type == dtypes_pb2.AstType.AST_LOGICAL


def test_json_schema_to_sql_builder_payload_supports_request_primary_keys():
    _, dtypes = json_schema_to_sql_builder_payload(
        {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
            },
        },
        ["id"],
    )

    assert "PRIMARY KEY" in dtypes["id"]["extra"]


def test_json_schema_to_sql_builder_payload_normalizes_property_names():
    cols, dtypes = json_schema_to_sql_builder_payload(
        {
            "type": "object",
            "required": ["NOMBRE COMPLETO"],
            "properties": {
                "NOMBRE COMPLETO": {"type": "string", "maxLength": 100},
                "Edad#": {"type": "integer"},
            },
        },
        primary_keys=["Edad#"],
        fill_spaces="_",
    )

    assert set(dtypes.keys()) == {"nombre_completo", "edad"}
    assert set(cols.keys()) == {"nombre_completo", "edad"}
    assert "NOT NULL" in dtypes["nombre_completo"]["extra"]
    assert "PRIMARY KEY" in dtypes["edad"]["extra"]


def test_json_schema_to_sql_builder_payload_detects_name_collisions():
    try:
        json_schema_to_sql_builder_payload(
            {
                "type": "object",
                "properties": {
                    "Nombre Completo": {"type": "string"},
                    "Nombre  Completo": {"type": "string"},
                },
            }
        )
    except ValueError as exc:
        assert "collapse to the same standardized identifier" in str(exc)
        return

    assert False, "Expected ValueError when standardized names collide"


def test_json_schema_to_sql_builder_payload_validates_request_primary_keys():
    try:
        json_schema_to_sql_builder_payload(
            {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                },
            },
            ["missing_column"],
        )
    except ValueError as exc:
        assert "must exist in 'properties'" in str(exc)
        return

    assert False, "Expected ValueError for missing primary key column"


def test_read_json_returns_excel_like_response(monkeypatch):
    def _fake_generate_sql(_stub, _cols, _dtypes, table_name):
        return f"CREATE TABLE IF NOT EXISTS {table_name} (...);"

    app.dependency_overrides[get_sql_builder_stub] = lambda: (
        _FakeSQLBuilderStub()
    )
    monkeypatch.setattr("src.server_rest.generate_sql", _fake_generate_sql)

    client = TestClient(app)
    response = client.post(
        "/parser/json",
        json={
            "table_name": "users",
            "jsonschema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string", "maxLength": 255},
                },
            },
            "primary_keys": ["id"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "users": "CREATE TABLE IF NOT EXISTS users (...);"
    }

    app.dependency_overrides.clear()


def test_read_json_returns_400_for_invalid_schema(monkeypatch):
    app.dependency_overrides[get_sql_builder_stub] = lambda: (
        _FakeSQLBuilderStub()
    )
    monkeypatch.setattr(
        "src.server_rest.generate_sql",
        lambda *_: "this should not run",
    )

    client = TestClient(app)
    response = client.post(
        "/parser/json",
        json={
            "table_name": "users",
            "jsonschema": {"type": "array", "items": {"type": "string"}},
        },
    )

    assert response.status_code == 400
    assert "root type 'object'" in response.json()["detail"]

    app.dependency_overrides.clear()
