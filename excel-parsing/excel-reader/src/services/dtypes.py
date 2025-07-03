from typing import TypedDict


class CellData(TypedDict):
    """
    TypedDict for representing cell data in an Excel sheet.

    Attributes:
        cell (str): The cell coordinate (e.g., "A1").
        value (str | float | int | None): The value of the cell, which can be a string, float, int, or None.
        data_type (str): The data type of the cell value (e.g., "s", "n", etc.).
        is_formula (bool): Indicates whether the cell contains a formula.
    """

    cell: str
    value: str | float | int | None
    data_type: str
    is_formula: bool


class SpreadsheetContent(TypedDict):
    """
    TypedDict for representing the content of a spreadsheet.

    Attributes:
        raw_data (dict[str, dict[str, list[CellData]]]): The raw data extracted from the spreadsheet.
        columns (dict[str, list[str]]): A dictionary mapping sheet names to lists of column values.
        data (dict[str, dict[str, list[CellData]]]): A dictionary mapping sheet names to dictionaries of cell data.
    """

    raw_data: dict[str, dict[str, list[CellData]]]
    columns: dict[str, list[str]]
    data: dict[str, dict[str, list[CellData]]]
