from clients.formula_parser import dtypes_pb2
from typing import TypedDict, Literal, Optional


AstTypes = Literal[
    "binary-expression",  # e.g., "a + b"
    "cell-range",  # e.g., "A1:B2"
    "function",  # e.g., "SUM(A1:B2)"
    "cell",  # e.g., "A1"
    "number",  # e.g., 42
    "logical",  # e.g., true
    "text",  # e.g., "Hello, World!"
]

RefTypes = Literal[
    "relative",  # Obtained from a cell reference like "A1" or "B2"
    "absolute",  # Obtained from a cell reference like "$A$1" or "$B$2"
    "mixed",  # Obtained from a cell reference like "A$1" or "$B2"
]


class AST(TypedDict):
    """
    Represents an Abstract Syntax Tree (AST) node.
    Each node can represent a binary expression, a cell range,
    a function call, or a single cell reference in spreadsheet formulas.

    Attributes:
        type (AstTypes): The type of the AST node indicating its structure and purpose.
        operator (Optional[str]): The operator for binary expressions such as "+", "-", "*", "/".
            Only used when type indicates a binary expression.
        left (Optional["AST"]): The left operand for binary expressions, the range start for
            cell ranges, or the first argument for functions. Used for binary expressions,
            functions, and cell ranges.
        right (Optional["AST"]): The right operand for binary expressions, the range end for
            cell ranges, or additional arguments for functions. Used for binary expressions,
            functions, and cell ranges.
        arguments (Optional[list["AST"]]): A list of AST nodes representing the arguments
            passed to function calls. Only used when type indicates a function.
        name (Optional[str]): The name identifier of the function being called, such as
            "SUM", "AVERAGE", "COUNT". Only used for function type nodes.
        refType (Optional[str]): The type of cell reference indicating the range format,
            such as "A1:B2" for ranges or "A1" for single cells. Only used for cell
            reference type nodes.
        key (Optional[str]): The specific cell reference key, such as "A1", "B2", or
            "C3:D5". Only used for cell reference type nodes.
        value (Optional[float]): The numeric value for nodes representing numbers. Only used
            for number type nodes.
    """

    type: AstTypes
    operator: Optional[str]
    left: Optional["AST"]
    right: Optional["AST"]
    arguments: Optional[list["AST"]]
    name: Optional[str]
    refType: Optional[RefTypes]
    key: Optional[str]
    value: Optional[float | str | bool]


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
    ast: Optional[AST | dtypes_pb2.AST] = None


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
