from src.utils.formatting import standardize_string


def test_standardize_string_removes_special_chars_and_lowercases():
    assert standardize_string("Número# Cliente!") == "numero_cliente"


def test_standardize_string_uses_fill_spaces_parameter():
    assert standardize_string("My  Column Name", fill_spaces="--") == "my_column_name"


def test_standardize_string_prefixes_when_starts_with_digit():
    assert standardize_string("123 columna") == "_123_columna"


def test_standardize_string_returns_fallback_for_empty_result():
    assert standardize_string("###") == "unnamed"


def test_standardize_string_allows_removing_spaces_when_fill_empty():
    assert standardize_string("Total ventas", fill_spaces="") == "totalventas"
