from src.services.sql import get_sql_from_function


def test_get_sql_from_function_sum_uses_columns_array():
    args = [{"columns": ["c1", "c2", "c3"]}]
    assert get_sql_from_function("SUM", args) == "c1 + c2 + c3"


def test_get_sql_from_function_if_generates_case_when():
    args = [{"sql": "a > 0"}, {"sql": "1"}, {"sql": "0"}]
    assert (
        get_sql_from_function("IF", args) == "CASE WHEN a > 0 THEN 1 ELSE 0 END"
    )


def test_get_sql_from_function_and_joins_with_and():
    args = [{"sql": "a > 0"}, {"sql": "b > 0"}]
    assert get_sql_from_function("AND", args) == "a > 0 AND b > 0"


def test_get_sql_from_function_unknown_function_returns_marker():
    assert get_sql_from_function("FOO", []) == "UNSUPPORTED_FUNCTION(FOO)"
