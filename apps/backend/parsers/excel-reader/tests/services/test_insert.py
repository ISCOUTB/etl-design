from src.services.insert import create_sql_for_insertion


def test_create_sql_for_insertion_single_sheet(monkeypatch):
    # Excel input: one sheet, 2 non-formula columns, 2 rows
    monkeypatch.setattr(
        "src.services.insert.get_data_from_spreadsheet",
        lambda **_kwargs: {
            "columns": {
                "Sheet1": {
                    "A": {"name": "id", "is_formula": False},
                    "B": {"name": "name", "is_formula": False},
                }
            },
            "data": {
                "Sheet1": {
                    "A": [
                        {"value": 1},
                        {"value": 2},
                    ],
                    "B": [
                        {"value": "Alice"},
                        {"value": None},
                    ],
                }
            },
        },
    )

    result = create_sql_for_insertion(
        table_name="users",
        file_bytes=b"bytes",
        filename="users.xlsx",
    )

    sql = result["Sheet1"]
    assert sql.startswith("INSERT INTO users (id, name) VALUES")
    assert "(1, 'Alice')" in sql
    assert "(2, NULL)" in sql


def test_create_sql_for_insertion_multiple_sheets_adds_suffix(monkeypatch):
    # Excel input: two sheets -> per-sheet table names
    monkeypatch.setattr(
        "src.services.insert.get_data_from_spreadsheet",
        lambda **_kwargs: {
            "columns": {
                "Sheet1": {
                    "A": {"name": "id", "is_formula": False},
                },
                "Sheet2": {
                    "A": {"name": "id", "is_formula": False},
                },
            },
            "data": {
                "Sheet1": {"A": [{"value": 1}]},
                "Sheet2": {"A": [{"value": 2}]},
            },
        },
    )

    result = create_sql_for_insertion(
        table_name="users",
        file_bytes=b"bytes",
        filename="users.xlsx",
    )

    assert "INSERT INTO users_Sheet1" in result["Sheet1"]
    assert "INSERT INTO users_Sheet2" in result["Sheet2"]


def test_create_sql_for_insertion_ignores_formula_columns(monkeypatch):
    # Excel input: column B is formula -> should be ignored in INSERT
    monkeypatch.setattr(
        "src.services.insert.get_data_from_spreadsheet",
        lambda **_kwargs: {
            "columns": {
                "Sheet1": {
                    "A": {"name": "id", "is_formula": False},
                    "B": {"name": "total", "is_formula": True},
                }
            },
            "data": {
                "Sheet1": {
                    "A": [{"value": 1}],
                    "B": [{"value": 99}],
                }
            },
        },
    )

    result = create_sql_for_insertion(
        table_name="users",
        file_bytes=b"bytes",
        filename="users.xlsx",
    )

    sql = result["Sheet1"]
    assert "(id)" in sql
    assert "total" not in sql


def test_create_sql_for_insertion_with_truncate_wraps_atomic_swap(monkeypatch):
    # Excel input: truncate=True should create temp table and swap names
    monkeypatch.setattr(
        "src.services.insert.get_data_from_spreadsheet",
        lambda **_kwargs: {
            "columns": {
                "Sheet1": {
                    "A": {"name": "id", "is_formula": False},
                }
            },
            "data": {
                "Sheet1": {"A": [{"value": 1}]},
            },
        },
    )

    result = create_sql_for_insertion(
        table_name="users",
        file_bytes=b"bytes",
        filename="users.xlsx",
        truncate=True,
    )

    sql = result["Sheet1"]
    assert "CREATE TABLE users_temp (LIKE users INCLUDING ALL);" in sql
    assert "BEGIN;" in sql
    assert "ALTER TABLE users RENAME TO users_backup;" in sql
    assert "ALTER TABLE users_temp RENAME TO users;" in sql
    assert "DROP TABLE users_backup;" in sql
    assert sql.strip().endswith("COMMIT;")
