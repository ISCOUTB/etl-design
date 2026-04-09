import json
from pathlib import Path

import pytest

from src.utils import formula_parser_cli
from src.utils.formula_parser_cli import (
    FormulaParserError,
    get_ast,
    parse_formula,
)


class DummyCompletedProcess:
    def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_get_formula_parser_cli_path_missing_file_raises(monkeypatch):
    monkeypatch.setattr(formula_parser_cli.Path, "exists", lambda self: False)

    with pytest.raises(FileNotFoundError):
        formula_parser_cli._get_formula_parser_cli_path()


def test_parse_formula_success_with_direct_node_fallback(monkeypatch):
    monkeypatch.setattr(
        formula_parser_cli,
        "_get_formula_parser_cli_path",
        lambda: Path("/tmp/cli.cjs"),
    )

    calls = [
        DummyCompletedProcess("", "No module named 'node'", 1),
        DummyCompletedProcess(
            json.dumps(
                {
                    "formula": "=A1",
                    "tokens": [],
                    "ast": {"type": "cell", "key": "A1", "refType": "relative"},
                    "error": "",
                    "success": True,
                }
            )
        ),
    ]

    def fake_run(*args, **kwargs):
        return calls.pop(0)

    monkeypatch.setattr(formula_parser_cli.subprocess, "run", fake_run)

    result = parse_formula("=A1")
    assert result["success"] is True
    assert result["ast"] is not None
    assert result["ast"]["type"] == "cell"


def test_parse_formula_invalid_json_raises_error(monkeypatch):
    monkeypatch.setattr(
        formula_parser_cli,
        "_get_formula_parser_cli_path",
        lambda: Path("/tmp/cli.cjs"),
    )

    monkeypatch.setattr(
        formula_parser_cli.subprocess,
        "run",
        lambda *args, **kwargs: DummyCompletedProcess("not-json"),
    )

    with pytest.raises(FormulaParserError):
        parse_formula("=A1")


def test_get_ast_raises_when_parse_is_unsuccessful(monkeypatch):
    monkeypatch.setattr(
        formula_parser_cli,
        "parse_formula",
        lambda formula: {
            "formula": formula,
            "tokens": None,
            "ast": None,
            "error": "boom",
            "success": False,
        },
    )

    with pytest.raises(FormulaParserError, match="boom"):
        get_ast("=A1")


def test_get_ast_returns_ast_when_successful(monkeypatch):
    expected_ast = {"type": "cell", "key": "A1", "refType": "relative"}

    monkeypatch.setattr(
        formula_parser_cli,
        "parse_formula",
        lambda formula: {
            "formula": formula,
            "tokens": [],
            "ast": expected_ast,
            "error": "",
            "success": True,
        },
    )

    assert get_ast("=A1") == expected_ast
