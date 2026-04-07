from types import SimpleNamespace

from proto_utils.generated.parsers import (
    dtypes_pb2,
)

from src.services.parse_formulas import (
    generate_data,
    generate_ddl,
    generate_sql,
    parse_formula,
    parse_formulas,
    parse_formulas_with_ddl,
)


class _FakeFormulaStub:
    def __init__(self):
        self.last_formula = None

    def ParseFormula(self, request):
        self.last_formula = request.formula
        return SimpleNamespace(ast="FAKE_AST")


class _FakeDDLStub:
    def __init__(self):
        self.last_columns = None

    def GenerateDDL(self, request):
        self.last_columns = dict(request.columns)
        return SimpleNamespace(sql="col_a + 1", payload="raw-ddl")


class _FakeSQLBuilderStub:
    def BuildSQL(self, _request):
        return SimpleNamespace()


def test_parse_formula_builds_request_and_returns_ast():
    # Excel input: single formula cell '=A1+1'
    stub = _FakeFormulaStub()

    result = parse_formula(stub, "A1+1")

    assert result == "FAKE_AST"
    assert stub.last_formula == "A1+1"


def test_generate_ddl_returns_sql_or_raw_response():
    # Excel input: generated AST for one computed column
    stub = _FakeDDLStub()

    sql = generate_ddl(stub, dtypes_pb2.AST(), {"A": "amount"}, raw=False)
    raw = generate_ddl(stub, dtypes_pb2.AST(), {"A": "amount"}, raw=True)

    assert sql == "col_a + 1"
    assert getattr(raw, "payload") == "raw-ddl"
    assert stub.last_columns == {"A": "amount"}


def test_generate_sql_concatenates_levels(monkeypatch):
    # Excel input: level 0 + level 1 generated SQL from SQL-Builder
    monkeypatch.setattr(
        "src.services.parse_formulas.SQLBuilderSerde.deserialize_build_sql_response",
        lambda _response: {
            "content": {
                0: {
                    "sql_content": [
                        {"sql": "CREATE TABLE test (id INTEGER);"},
                    ]
                },
                1: {
                    "sql_content": [
                        {
                            "sql": "ALTER TABLE test ADD COLUMN total INTEGER GENERATED ALWAYS AS (id + 1) STORED;"
                        }
                    ]
                },
            }
        },
    )

    sql = generate_sql(
        _FakeSQLBuilderStub(),
        cols={},
        dtypes={"id": {"type": "INTEGER", "extra": ""}},
        table_name="test",
    )

    assert sql.startswith("CREATE TABLE test")
    assert "\nALTER TABLE test ADD COLUMN" in sql


def test_generate_data_yields_first_cell_per_column():
    data = {
        "Sheet1": {
            "A": [
                {
                    "cell": "A2",
                    "value": 10,
                    "data_type": "n",
                    "is_formula": False,
                },
                {
                    "cell": "A3",
                    "value": 20,
                    "data_type": "n",
                    "is_formula": False,
                },
            ],
            "B": [
                {
                    "cell": "B2",
                    "value": "name",
                    "data_type": "s",
                    "is_formula": False,
                }
            ],
        }
    }

    rows = list(generate_data(data))

    assert len(rows) == 2
    assert rows[0]["index"] == "0"
    assert rows[0]["cell"]["cell"] == "A2"
    assert rows[1]["cell"]["cell"] == "B2"


def test_parse_formulas_quotes_strings_and_attaches_ast(monkeypatch):
    # Excel input: one string cell and one numeric cell
    monkeypatch.setattr(
        "src.services.parse_formulas.get_data_from_spreadsheet",
        lambda *_args, **_kwargs: {
            "columns": {
                "Sheet1": {
                    "A": {"name": "name", "is_formula": False},
                    "B": {"name": "age", "is_formula": False},
                }
            },
            "data": {
                "Sheet1": {
                    "A": [
                        {
                            "cell": "A2",
                            "value": "Alice",
                            "data_type": "s",
                            "is_formula": False,
                        }
                    ],
                    "B": [
                        {
                            "cell": "B2",
                            "value": 30,
                            "data_type": "n",
                            "is_formula": False,
                        }
                    ],
                }
            },
        },
    )

    seen_formulas = []

    def _fake_parse_formula(_stub, formula):
        seen_formulas.append(formula)
        return "AST" if '"' in formula else "AST_NUM"

    monkeypatch.setattr(
        "src.services.parse_formulas.parse_formula", _fake_parse_formula
    )

    result = parse_formulas(
        formula_parser_stub=object(),
        filename="users.xlsx",
        file_bytes=b"bytes",
    )

    sheet = result["result"]["Sheet1"]
    assert sheet["A"][0]["value"] == '"Alice"'
    assert sheet["A"][0]["ast"] == "AST"
    assert sheet["B"][0]["ast"] == "AST_NUM"
    assert '"Alice"' in seen_formulas
    assert "30" in seen_formulas


def test_parse_formulas_with_ddl_enriches_cells(monkeypatch):
    # Excel input: one computed column with AST already parsed
    ast = dtypes_pb2.AST()

    monkeypatch.setattr(
        "src.services.parse_formulas.parse_formulas",
        lambda **_kwargs: {
            "result": {
                "Sheet1": {
                    "A": [
                        {
                            "cell": "A2",
                            "value": 10,
                            "data_type": "n",
                            "is_formula": False,
                            "ast": ast,
                        }
                    ]
                }
            },
            "columns": {
                "Sheet1": {
                    "A": {"name": "amount", "is_formula": False},
                }
            },
        },
    )

    monkeypatch.setattr(
        "src.services.parse_formulas.generate_ddl",
        lambda *_args, **_kwargs: "RAW_DDL",
    )
    monkeypatch.setattr(
        "src.services.parse_formulas.DTypesSerde.deserialize_ast",
        lambda _ast: {"type": "number", "sql": "10"},
    )

    result = parse_formulas_with_ddl(
        formula_parser_stub=object(),
        ddl_generator_stub=object(),
        filename="users.xlsx",
        file_bytes=b"bytes",
    )

    cell = result["result"]["Sheet1"]["A"][0]
    assert cell["sql"] == "RAW_DDL"
    assert cell["ast"] == {"type": "number", "sql": "10"}
