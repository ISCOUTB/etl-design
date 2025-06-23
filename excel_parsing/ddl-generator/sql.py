from typing import List
from dtypes import CellRangeMapsOutput, AllOutputs, SingleOutput, ComplexOutput


def get_sql_from_function(func_name: str, args: List[AllOutputs]) -> str:
    if func_name == "SUM":
        # Here we assume that references are in the form of "A1", "B1", etc.
        args: CellRangeMapsOutput = args[0]
        cols = args["columns"]
        sql = " + ".join(cols)
        return sql

    if func_name == "IF":
        condition: ComplexOutput = args[0]
        true_value: SingleOutput = args[1]
        false_value: SingleOutput = args[2]
        sql = (
            f"CASE WHEN {condition['sql']} THEN {true_value['sql']} "
            + f"ELSE {false_value['sql']} END"
        )
        return sql

    if func_name == "AND":
        sql = " AND ".join(arg["sql"] for arg in args)
        return sql

    # Add more function mappings here as needed

    return f"UNSUPPORTED_FUNCTION({func_name})"
