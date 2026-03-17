# type:ignore
import pytest

from src.services.ddl_generator import generate_ddl
from src.services.generator import (
    MAPS,
    binary_maps,
    cell_maps,
    cell_range_maps,
    function_maps,
    logical_maps,
    number_maps,
    text_maps,
    unary_maps,
)


def test_cell_maps_success_with_relative_reference():
    # Excel input: =A1
    ast = {"type": "cell", "refType": "relative", "key": "A1"}
    result = cell_maps(ast, {"A": "col_a"})

    assert result["cell"] == "A1"
    assert result["column"] == "col_a"
    assert result["sql"] == "col_a"
    assert result["error"] is None


def test_cell_maps_missing_column_returns_error_and_empty_sql():
    # Excel input: =Z1
    ast = {"type": "cell", "refType": "relative", "key": "Z1"}
    result = cell_maps(ast, {"A": "col_a"})

    assert result["column"] == ""
    assert result["sql"] == ""
    assert "KeyError" in result["error"]


def test_cell_maps_removes_dollar_signs():
    # Excel input: =$A$10
    ast = {"type": "cell", "refType": "absolute", "key": "$A$10"}
    result = cell_maps(ast, {"A": "col_a"})

    assert result["cell"] == "A10"
    assert result["column"] == "col_a"


def test_cell_range_maps_success_returns_column_range_sql():
    # Excel input: =A1:C1
    ast = {
        "type": "cell-range",
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "cell", "refType": "relative", "key": "C1"},
    }
    result = cell_range_maps(ast, {"A": "c1", "B": "c2", "C": "c3"})

    assert result["cells"] == ["A", "B", "C"]
    assert result["columns"] == ["c1", "c2", "c3"]
    assert result["sql"] == "c1, c2, c3"
    assert result["error"] is None


def test_cell_range_maps_missing_column_marks_error():
    # Excel input: =A1:C1
    ast = {
        "type": "cell-range",
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "cell", "refType": "relative", "key": "C1"},
    }
    result = cell_range_maps(ast, {"A": "c1"})

    assert result["columns"] == []
    assert result["sql"] == ""
    assert "KeyError" in result["error"]


def test_number_maps_formats_as_string_sql():
    result = number_maps({"type": "number", "value": 42}, {})
    assert result["value"] == 42.0
    assert result["sql"] == "42"


def test_logical_maps_handles_string_true_false():
    true_result = logical_maps({"type": "logical", "value": "true"}, {})
    false_result = logical_maps({"type": "logical", "value": "false"}, {})

    assert true_result["value"] is True
    assert true_result["sql"] == "TRUE"
    assert false_result["value"] is False
    assert false_result["sql"] == "FALSE"


def test_text_maps_wraps_and_normalizes_quotes():
    result = text_maps({"type": "text", "value": 'a "quoted" value'}, {})
    assert result["sql"] == "'a 'quoted' value'"


def test_binary_maps_builds_nested_sql():
    # Excel input: =A1+5
    ast = {
        "type": "binary-expression",
        "operator": "+",
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "number", "value": 5},
    }
    result = binary_maps(ast, {"A": "amount"})

    assert result["sql"] == "(amount) + (5)"


@pytest.mark.parametrize(
    "operator, expected_sql",
    [
        ("=", "(left_col) IS NOT DISTINCT FROM (right_col)"),
        ("<>", "(left_col) IS DISTINCT FROM (right_col)"),
        (">", "(left_col) > (right_col)"),
        ("<", "(left_col) < (right_col)"),
        (">=", "(left_col) >= (right_col)"),
        ("<=", "(left_col) <= (right_col)"),
    ],
)
def test_binary_maps_supports_comparison_operators(operator, expected_sql):
    # Excel input template: =A1{operator}B1
    ast = {
        "type": "binary-expression",
        "operator": operator,
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "cell", "refType": "relative", "key": "B1"},
    }

    result = binary_maps(ast, {"A": "left_col", "B": "right_col"})

    assert result["operator"] == operator
    assert result["sql"] == expected_sql


def test_unary_maps_uses_operand_sql():
    # Excel input: =-7
    ast = {
        "type": "unary-expression",
        "operator": "-",
        "operand": {"type": "number", "value": 7},
    }
    result = unary_maps(ast, {})

    assert result["sql"] == "-(7)"


def test_function_maps_sum_with_cell_range():
    # Excel input: =SUM(A1:B1)
    ast = {
        "type": "function",
        "name": "SUM",
        "arguments": [
            {
                "type": "cell-range",
                "left": {"type": "cell", "refType": "relative", "key": "A1"},
                "right": {"type": "cell", "refType": "relative", "key": "B1"},
            }
        ],
    }
    result = function_maps(ast, {"A": "x", "B": "y"})

    assert result["name"] == "SUM"
    assert result["sql"] == "x + y"


def test_function_maps_if_with_equal_condition_generates_case_when():
    # Excel input: =IF(A1=B1,1,0)
    ast = {
        "type": "function",
        "name": "IF",
        "arguments": [
            {
                "type": "binary-expression",
                "operator": "=",
                "left": {"type": "cell", "refType": "relative", "key": "A1"},
                "right": {"type": "cell", "refType": "relative", "key": "B1"},
            },
            {"type": "number", "value": 1},
            {"type": "number", "value": 0},
        ],
    }

    result = function_maps(ast, {"A": "left_col", "B": "right_col"})

    assert (
        result["sql"]
        == "CASE WHEN (left_col) IS NOT DISTINCT FROM (right_col) THEN 1 ELSE 0 END"
    )


def test_function_maps_if_with_not_equal_condition_generates_case_when():
    # Excel input: =IF(A1<>B1,"different","equal")
    ast = {
        "type": "function",
        "name": "IF",
        "arguments": [
            {
                "type": "binary-expression",
                "operator": "<>",
                "left": {"type": "cell", "refType": "relative", "key": "A1"},
                "right": {"type": "cell", "refType": "relative", "key": "B1"},
            },
            {"type": "text", "value": "different"},
            {"type": "text", "value": "equal"},
        ],
    }

    result = function_maps(ast, {"A": "left_col", "B": "right_col"})

    assert (
        result["sql"]
        == "CASE WHEN (left_col) IS DISTINCT FROM (right_col) THEN 'different' ELSE 'equal' END"
    )


def test_binary_maps_equal_should_be_null_safe_in_sql():
    # Excel input: =A1=B1
    ast = {
        "type": "binary-expression",
        "operator": "=",
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "cell", "refType": "relative", "key": "B1"},
    }

    result = binary_maps(ast, {"A": "left_col", "B": "right_col"})

    # Null-safe equality better matches Excel-like semantics for nullable columns.
    assert result["sql"] == "(left_col) IS NOT DISTINCT FROM (right_col)"


def test_binary_maps_not_equal_should_be_null_safe_in_sql():
    # Excel input: =A1<>B1
    ast = {
        "type": "binary-expression",
        "operator": "<>",
        "left": {"type": "cell", "refType": "relative", "key": "A1"},
        "right": {"type": "cell", "refType": "relative", "key": "B1"},
    }

    result = binary_maps(ast, {"A": "left_col", "B": "right_col"})

    # Null-safe inequality prevents NULL comparisons from becoming UNKNOWN.
    assert result["sql"] == "(left_col) IS DISTINCT FROM (right_col)"


def test_generate_ddl_dispatches_by_ast_type():
    # Excel input: =A1
    result = generate_ddl(
        {
            "ast": {"type": "cell", "refType": "relative", "key": "A1"},
            "columns": {"A": "col_a"},
        }
    )

    assert result["sql"] == "col_a"


def test_function_maps_if_with_and_condition_and_sum_then_branch():
    # Excel input: =IF(AND(A1<>B1,C1>=10),SUM(D1:F1),0)
    ast = {
        "type": "function",
        "name": "IF",
        "arguments": [
            {
                "type": "function",
                "name": "AND",
                "arguments": [
                    {
                        "type": "binary-expression",
                        "operator": "<>",
                        "left": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "A1",
                        },
                        "right": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "B1",
                        },
                    },
                    {
                        "type": "binary-expression",
                        "operator": ">=",
                        "left": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "C1",
                        },
                        "right": {"type": "number", "value": 10},
                    },
                ],
            },
            {
                "type": "function",
                "name": "SUM",
                "arguments": [
                    {
                        "type": "cell-range",
                        "left": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "D1",
                        },
                        "right": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "F1",
                        },
                    }
                ],
            },
            {"type": "number", "value": 0},
        ],
    }

    columns = {
        "A": "left_col",
        "B": "right_col",
        "C": "score_col",
        "D": "jan",
        "E": "feb",
        "F": "mar",
    }

    result = function_maps(ast, columns)

    assert result["sql"] == (
        "CASE WHEN (left_col) IS DISTINCT FROM (right_col) "
        "AND (score_col) >= (10) THEN jan + feb + mar ELSE 0 END"
    )


def test_function_maps_nested_if_builds_nested_case_when_sql():
    # Excel input: =IF(A1=B1,IF(C1<=D1,"ok","bad"),"skip")
    ast = {
        "type": "function",
        "name": "IF",
        "arguments": [
            {
                "type": "binary-expression",
                "operator": "=",
                "left": {"type": "cell", "refType": "relative", "key": "A1"},
                "right": {"type": "cell", "refType": "relative", "key": "B1"},
            },
            {
                "type": "function",
                "name": "IF",
                "arguments": [
                    {
                        "type": "binary-expression",
                        "operator": "<=",
                        "left": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "C1",
                        },
                        "right": {
                            "type": "cell",
                            "refType": "relative",
                            "key": "D1",
                        },
                    },
                    {"type": "text", "value": "ok"},
                    {"type": "text", "value": "bad"},
                ],
            },
            {"type": "text", "value": "skip"},
        ],
    }

    result = function_maps(
        ast,
        {"A": "a_col", "B": "b_col", "C": "c_col", "D": "d_col"},
    )

    assert result["sql"] == (
        "CASE WHEN (a_col) IS NOT DISTINCT FROM (b_col) THEN "
        "CASE WHEN (c_col) <= (d_col) THEN 'ok' ELSE 'bad' END "
        "ELSE 'skip' END"
    )


def test_generate_ddl_handles_complex_binary_with_unary_operand():
    # Excel input: =(A1+B1)*-(C1-2)
    ast = {
        "type": "binary-expression",
        "operator": "*",
        "left": {
            "type": "binary-expression",
            "operator": "+",
            "left": {"type": "cell", "refType": "relative", "key": "A1"},
            "right": {"type": "cell", "refType": "relative", "key": "B1"},
        },
        "right": {
            "type": "unary-expression",
            "operator": "-",
            "operand": {
                "type": "binary-expression",
                "operator": "-",
                "left": {"type": "cell", "refType": "relative", "key": "C1"},
                "right": {"type": "number", "value": 2},
            },
        },
    }

    result = generate_ddl(
        {
            "ast": ast,
            "columns": {"A": "x", "B": "y", "C": "z"},
        }
    )

    assert result["sql"] == "((x) + (y)) * (-((z) - (2)))"


def test_maps_contains_expected_handlers():
    for ast_type in {
        "binary-expression",
        "cell-range",
        "function",
        "cell",
        "number",
        "logical",
        "text",
        "unary-expression",
    }:
        assert ast_type in MAPS


def test_map_functions_raise_value_error_for_wrong_type():
    with pytest.raises(ValueError):
        cell_maps({"type": "number", "value": 1}, {})

    with pytest.raises(ValueError):
        binary_maps({"type": "cell", "key": "A1", "refType": "relative"}, {})

    with pytest.raises(ValueError):
        function_maps({"type": "text", "value": "x"}, {})

    with pytest.raises(ValueError):
        number_maps({"type": "text", "value": "x"}, {})

    with pytest.raises(ValueError):
        logical_maps({"type": "text", "value": "x"}, {})

    with pytest.raises(ValueError):
        text_maps({"type": "number", "value": 1}, {})

    with pytest.raises(ValueError):
        unary_maps({"type": "number", "value": 1}, {})
