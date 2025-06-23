from sql import get_sql_from_function
from utils import get_column_range, get_column_from_cell

from typing import Dict, Callable
from dtypes import (
    AST,
    AstTypes,
    CellMapsOutput,
    CellRangeMapsOutput,
    NumberMapsOutput,
    BinaryExpressionMapsOutput,
    FunctionMapsOutput,
)


MAPS: Dict[AstTypes, Callable] = {
    "binary-expression": lambda ast, columns: binary_maps(ast, columns),
    "cell-range": lambda ast, columns: cell_range_maps(ast, columns),
    "function": lambda ast, columns: function_maps(ast, columns),
    "cell": lambda ast, columns: cell_maps(ast, columns),
    "number": lambda ast, columns: number_maps(ast, columns),
    "logical": lambda ast, columns: logical_maps(ast, columns),
}


def binary_maps(ast: AST, columns: Dict[str, str]) -> BinaryExpressionMapsOutput:
    if ast["type"] != "binary-expression":
        raise ValueError("AST must be of type 'binary-expression'")

    left = MAPS[ast["left"]["type"]](ast["left"], columns)
    right = MAPS[ast["right"]["type"]](ast["right"], columns)

    return {
        "type": "binary-expression",
        "operator": ast["operator"],
        "left": left,
        "right": right,
        "sql": f"({left['sql']}) {ast['operator']} ({right['sql']})",
    }


def function_maps(ast: AST, columns: Dict[str, str]) -> FunctionMapsOutput:
    if ast["type"] != "function":
        raise ValueError("AST must be of type 'function'")

    funtion_name = ast["name"]
    args_raw = ast.get("arguments", [])
    args = [MAPS[arg["type"]](arg, columns) for arg in args_raw]
    sql = get_sql_from_function(funtion_name, args)

    return {"type": "function", "arguments": args, "name": funtion_name, "sql": sql}


def cell_range_maps(ast: AST, columns: Dict[str, str]) -> CellRangeMapsOutput:
    if ast["type"] != "cell-range":
        raise ValueError("AST must be of type 'cell-range'")

    start_cell = cell_maps(ast["left"], columns)["cell"]
    end_cell = cell_maps(ast["right"], columns)["cell"]
    range_cell = get_column_range(
        get_column_from_cell(start_cell), get_column_from_cell(end_cell)
    )
    try:
        columns_range = [columns[col] for col in range_cell]
        error = None
    except KeyError as e:
        columns_range = []
        error = repr(e)

    return {
        "type": "cell-range",
        "start": start_cell,
        "end": end_cell,
        "cells": range_cell,
        "columns": columns_range,
        "error": error,
    }


def cell_maps(ast: AST, columns: Dict[str, str]) -> CellMapsOutput:
    if ast["type"] != "cell":
        raise ValueError("AST must be of type 'cell'")

    cell = ast["key"].replace("$", "")
    try:
        column = get_column_from_cell(cell)
        column = columns[column]
        error = None
    except IndexError as e:
        column = ""
        error = repr(e)

    return {
        "type": "cell",
        "cell": cell,
        "refType": ast["refType"],
        "column": column,
        "error": error,
        "sql": column,
    }


def number_maps(ast: AST, _) -> NumberMapsOutput:
    if ast["type"] != "number":
        raise ValueError("AST must be of type 'number'")

    return {"type": "number", "value": float(ast["value"]), "sql": ast["value"]}


def logical_maps(ast: AST, _) -> CellMapsOutput:
    if ast["type"] != "logical":
        raise ValueError("AST must be of type 'logical'")

    value = str(ast["value"]).lower() == "true"  # Adjust depending on its received value
    return {
        "type": "logical",
        "value": value,
        "sql": str(value).upper(),
    }
