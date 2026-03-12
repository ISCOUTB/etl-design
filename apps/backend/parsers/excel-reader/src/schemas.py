from enum import Enum
from typing import Any, Dict, Generic, Optional, Self, TypedDict, TypeVar

from proto_utils.generated.parsers import ddl_generator_pb2, dtypes_pb2
from proto_utils.parsers.dtypes import AST
from pydantic import BaseModel, Field, model_validator


class CellData(TypedDict):
    """
    TypedDict for representing cell data in an Excel sheet.

    Attributes:
        cell (str): The cell coordinate (e.g., "A1").
        value (str | float | int | None): The value of the cell, which can be a string, float, int, or None.
        data_type (str): The data type of the cell value (e.g., "s", "n", etc.).
        is_formula (bool): Indicates whether the cell contains a formula.
        ast (Optional[AST | dtypes_pb2.AST]): The Abstract Syntax Tree representation of the formula,
            if applicable. This can be either a custom AST or a protobuf AST.
        sql (Optional[str]): The SQL representation of the cell value, typically used for database operations.
    """

    cell: str
    value: str | float | int | None
    data_type: str
    is_formula: bool
    ast: Optional[AST | dtypes_pb2.AST] = None
    sql: Optional[str | ddl_generator_pb2.DDLResponse] = None


class ColumnMetadata(TypedDict):
    """
    TypedDict for representing metadata about a column in an Excel sheet.

    Attributes:
        name (str): The name of the column, typically derived from the first cell in the column.
        is_formula (bool): Indicates whether the column contains any formulas. This can be used
            to identify columns that require special handling when generating SQL or performing
            data transformations.
    """

    name: str
    is_formula: bool


ColumnsInfo = Dict[str, Dict[str, ColumnMetadata]]
DataInfo = Dict[str, Dict[str, list[CellData]]]


class SpreadsheetContent(TypedDict):
    """
    TypedDict for representing the content of a spreadsheet.

    Attributes:
        raw_data (DataInfo): The raw data extracted from the spreadsheet.
        columns (Dict[str, Dict[str, str]]): A Dictionary mapping sheet names to lists of column values.
        data (DataInfo): A Dictionary mapping sheet names to Dictionaries of cell data.
    """

    raw_data: DataInfo
    columns: ColumnsInfo
    data: DataInfo


class ParseFormulasResult(TypedDict):
    """
    TypedDict for representing the result of parsing formulas in a spreadsheet.

    Attributes:
        result (DataInfo): A Dictionary mapping sheet names to Dictionaries of cell data with parsed formulas.
        columns (ColumnsInfo): A Dictionary mapping sheet names to lists of column values.
    """

    result: DataInfo
    columns: ColumnsInfo


class JSONSchemaRequest(BaseModel):
    jsonschema: Dict[str, Any]
    table_name: str
    primary_keys: list[str] = Field(default_factory=list)


class JSONSchemaColumn(TypedDict):
    type: str
    extra: str


JSONSchemaDTypes = Dict[str, Dict[str, str]]


NumVar = TypeVar("NumVar", int, float)


class DtypesEnum(Enum):
    """
    Enum for supported data types in the spreadsheet.
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"


class NumberConstraints(BaseModel, Generic[NumVar]):
    minimum: Optional[NumVar] = None
    maximum: Optional[NumVar] = None
    exclusive_minimum: bool = False
    exclusive_maximum: bool = False
    multiple_of: Optional[NumVar] = None


class IntegerConstraints(NumberConstraints[int]):
    pass


class FloatConstraints(NumberConstraints[float]):
    pass


class StringConstraints(BaseModel):
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None


class SpreadsheetDtypesSchema(BaseModel):
    dtype: DtypesEnum
    unique: bool = False
    optional: bool = True
    primary_key: bool = False
    constraints: Optional[NumberConstraints | StringConstraints] = None

    @model_validator(mode="after")
    def validate_constraint(self) -> Self:
        match self.dtype:
            case DtypesEnum.INTEGER:
                if self.constraints and not isinstance(
                    self.constraints, IntegerConstraints
                ):
                    raise ValueError(
                        "Constraints for integer types must be of type IntegerConstraints"
                    )
            case DtypesEnum.FLOAT | DtypesEnum.DOUBLE:
                if self.constraints and not isinstance(
                    self.constraints, FloatConstraints
                ):
                    raise ValueError(
                        "Constraints for float/double types must be of type FloatConstraints"
                    )
            case DtypesEnum.STRING:
                if self.constraints and not isinstance(
                    self.constraints, StringConstraints
                ):
                    raise ValueError(
                        "Constraints for string types must be of type StringConstraints"
                    )
            case DtypesEnum.BOOLEAN:
                if self.constraints is not None:
                    raise ValueError(
                        "Boolean type does not support constraints"
                    )

        return self


ColumnName = str
ColumnDtypesSchema = Dict[ColumnName, SpreadsheetDtypesSchema]
