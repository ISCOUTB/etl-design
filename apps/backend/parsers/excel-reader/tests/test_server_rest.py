import json

from fastapi.testclient import TestClient

from src.server_rest import app
from src.utils.deps import (
    get_ddl_generator_stub,
    get_formula_parser_stub,
    get_sql_builder_stub,
)


class _FakeFormulaParserStub:
    pass


class _FakeDDLGeneratorStub:
    pass


class _FakeSQLBuilderStub:
    pass


def _override_dependencies() -> None:
    app.dependency_overrides[get_formula_parser_stub] = lambda: (
        _FakeFormulaParserStub()
    )
    app.dependency_overrides[get_ddl_generator_stub] = lambda: (
        _FakeDDLGeneratorStub()
    )
    app.dependency_overrides[get_sql_builder_stub] = lambda: (
        _FakeSQLBuilderStub()
    )


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_read_excel_orchestrates_services_single_sheet(monkeypatch):
    # Excel input: one sheet (Sheet1), cols A=id, B=name
    called_tables = []

    def _fake_parse_formulas_with_ddl(**_kwargs):
        return {
            "result": {
                "Sheet1": {
                    "A": [{"sql": "ddl_id"}],
                    "B": [{"sql": "ddl_name"}],
                }
            },
            "columns": {
                "Sheet1": {
                    "A": {"name": "id", "is_formula": False},
                    "B": {"name": "name", "is_formula": False},
                }
            },
        }

    def _fake_generate_sql(*args, **kwargs):
        # args: stub, cols, dtypes, table_name, [scheme]
        cols_arg = args[1] if len(args) > 1 else kwargs.get("cols")
        table_name = args[3] if len(args) > 3 else kwargs.get("table_name")
        called_tables.append(table_name)
        assert cols_arg == {"id": "ddl_id", "name": "ddl_name"}
        return f"CREATE TABLE IF NOT EXISTS {table_name} (...);"

    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        _fake_parse_formulas_with_ddl,
    )
    monkeypatch.setattr("src.server_rest.generate_sql", _fake_generate_sql)

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "dtypes_str": json.dumps(
                {
                    "Sheet1": {
                        "A": {"dtype": "integer", "optional": False},
                        "B": {"dtype": "string", "optional": True},
                    }
                }
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "users": "CREATE TABLE IF NOT EXISTS users (...);"
    }
    assert called_tables == ["users"]

    _clear_overrides()


def test_read_excel_forwards_scheme_to_sql_builder(monkeypatch):
    # Excel input: single sheet, schema should be forwarded to SQL builder
    called_kwargs = {}

    def _fake_parse_formulas_with_ddl(**_kwargs):
        return {
            "result": {
                "Sheet1": {"A": [{"sql": "ddl_id"}]},
            },
            "columns": {
                "Sheet1": {"A": {"name": "id", "is_formula": False}},
            },
        }

    def _fake_generate_sql(*args, **kwargs):
        # capture positional table_name and scheme as SQLBuilder is called with positional args
        if len(args) > 3:
            called_kwargs["table_name"] = args[3]
        if len(args) > 4:
            called_kwargs["scheme"] = args[4]
        called_kwargs.update(kwargs)
        return "CREATE SCHEMA IF NOT EXISTS auth;\nCREATE TABLE IF NOT EXISTS auth.users (id INTEGER);"

    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        _fake_parse_formulas_with_ddl,
    )
    monkeypatch.setattr("src.server_rest.generate_sql", _fake_generate_sql)

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "scheme": "auth",
            "dtypes_str": json.dumps(
                {
                    "Sheet1": {
                        "A": {"dtype": "integer", "optional": False},
                    }
                }
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "users": "CREATE SCHEMA IF NOT EXISTS auth;\nCREATE TABLE IF NOT EXISTS auth.users (id INTEGER);"
    }
    assert called_kwargs["table_name"] == "users"
    assert called_kwargs["scheme"] == "auth"

    _clear_overrides()


def test_read_excel_orchestrates_services_multiple_sheets(monkeypatch):
    # Excel input: two sheets (Sheet1, Sheet2)
    called_tables = []

    def _fake_parse_formulas_with_ddl(**_kwargs):
        return {
            "result": {
                "Sheet1": {"A": [{"sql": "ddl_a1"}]},
                "Sheet2": {"A": [{"sql": "ddl_a2"}]},
            },
            "columns": {
                "Sheet1": {"A": {"name": "id", "is_formula": False}},
                "Sheet2": {"A": {"name": "id", "is_formula": False}},
            },
        }

    def _fake_generate_sql(*args, **kwargs):
        table_name = args[3] if len(args) > 3 else kwargs.get("table_name")
        called_tables.append(table_name)
        return f"SQL::{table_name}"

    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        _fake_parse_formulas_with_ddl,
    )
    monkeypatch.setattr("src.server_rest.generate_sql", _fake_generate_sql)

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "dtypes_str": json.dumps(
                {
                    "Sheet1": {"A": {"dtype": "integer"}},
                    "Sheet2": {"A": {"dtype": "integer"}},
                }
            ),
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "Sheet1": "SQL::users_sheet1",
        "Sheet2": "SQL::users_sheet2",
    }
    assert called_tables == ["users_sheet1", "users_sheet2"]

    _clear_overrides()


def test_read_excel_returns_400_on_empty_file(monkeypatch):
    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        lambda **_kwargs: {"result": {}, "columns": {}},
    )

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "dtypes_str": json.dumps({"Sheet1": {"A": {"dtype": "integer"}}}),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File content is empty"

    _clear_overrides()


def test_read_excel_returns_400_on_invalid_dtypes_json(monkeypatch):
    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        lambda **_kwargs: {"result": {}, "columns": {}},
    )

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "dtypes_str": "not-a-json",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON format for dtypes"

    _clear_overrides()


def test_read_excel_returns_400_on_sheet_mismatch(monkeypatch):
    def _fake_parse_formulas_with_ddl(**_kwargs):
        return {
            "result": {
                "Sheet1": {"A": [{"sql": "ddl_a1"}]},
                "Sheet2": {"A": [{"sql": "ddl_a2"}]},
            },
            "columns": {
                "Sheet1": {"A": {"name": "id", "is_formula": False}},
                "Sheet2": {"A": {"name": "id", "is_formula": False}},
            },
        }

    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.parse_formulas_with_ddl",
        _fake_parse_formulas_with_ddl,
    )
    monkeypatch.setattr(
        "src.server_rest.generate_sql",
        lambda *_args, **_kwargs: "SHOULD_NOT_RUN",
    )

    client = TestClient(app)
    response = client.post(
        "/parser/excel",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "table_name": "users",
            "dtypes_str": json.dumps(
                {
                    "Sheet1": {"A": {"dtype": "integer"}},
                }
            ),
        },
    )

    assert response.status_code == 400
    assert (
        "Mismatch between sheets in DDLs and dtypes"
        in response.json()["detail"]
    )

    _clear_overrides()


def test_read_json_normalizes_blank_table_name(monkeypatch):
    called_tables = []

    def _fake_generate_sql(*args, **kwargs):
        table_name = args[3] if len(args) > 3 else kwargs.get("table_name")
        called_tables.append(table_name)
        return f"CREATE TABLE IF NOT EXISTS {table_name} (...);"

    _override_dependencies()
    monkeypatch.setattr(
        "src.server_rest.generate_sql",
        _fake_generate_sql,
    )

    client = TestClient(app)
    response = client.post(
        "/parser/json",
        json={
            "table_name": "   ",
            "jsonschema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                },
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "unnamed": "CREATE TABLE IF NOT EXISTS unnamed (...);"
    }
    assert called_tables == ["unnamed"]

    _clear_overrides()


def test_insert_sql_single_sheet_uses_table_name_key(monkeypatch):
    # Excel input: one sheet, insertion SQL already built in service layer
    monkeypatch.setattr(
        "src.server_rest.create_sql_for_insertion",
        lambda *_args, **_kwargs: {"Sheet1": "INSERT INTO users ...;"},
    )

    client = TestClient(app)
    response = client.post(
        "/insert-sql",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"table_name": "users", "overwrite": "false"},
    )

    assert response.status_code == 200
    assert response.json() == {"users": "INSERT INTO users ...;"}


def test_insert_sql_with_scheme_uses_table_name_key(monkeypatch):
    monkeypatch.setattr(
        "src.server_rest.create_sql_for_insertion",
        lambda *_args, **_kwargs: {"Sheet1": "INSERT INTO auth.users ...;"},
    )

    client = TestClient(app)
    response = client.post(
        "/insert-sql",
        files={
            "spreadsheet": (
                "sample.xlsx",
                b"fake excel bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"table_name": "users", "scheme": "auth", "overwrite": "false"},
    )

    assert response.status_code == 200
    assert response.json() == {"users": "INSERT INTO auth.users ...;"}
