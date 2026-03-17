from src.services.utils import (
    excel_col_to_index,
    get_all_cells_from_range,
    get_column_from_cell,
    get_column_range,
    get_row_from_cell,
    get_rows_range,
    index_to_excel_col,
)


def test_get_row_from_cell_extracts_digits():
    assert get_row_from_cell("A1") == 1
    assert get_row_from_cell("BC25") == 25


def test_get_rows_range_inclusive():
    assert get_rows_range("A1", "A3") == [1, 2, 3]


def test_get_column_from_cell_extracts_letters():
    assert get_column_from_cell("A1") == "A"
    assert get_column_from_cell("BC25") == "BC"


def test_excel_col_to_index_and_back_roundtrip():
    assert excel_col_to_index("A") == 1
    assert excel_col_to_index("Z") == 26
    assert excel_col_to_index("AA") == 27
    assert index_to_excel_col(1) == "A"
    assert index_to_excel_col(26) == "Z"
    assert index_to_excel_col(27) == "AA"


def test_get_column_range_crosses_alphabet_boundary():
    assert get_column_range("Y", "AB") == ["Y", "Z", "AA", "AB"]


def test_get_all_cells_from_range_generates_cartesian_order():
    assert get_all_cells_from_range("A1", "B2") == ["A1", "A2", "B1", "B2"]
