from typing import List
from dtypes import AllOutputs

FUNCTION_SQL_MAP = {
    "SUM": lambda args: " + ".join(args[0]["columns"]),
    "IF": lambda args: f"CASE WHEN {args[0]['sql']} THEN {args[1]['sql']} ELSE {args[2]['sql']} END",
    "AND": lambda args: " AND ".join(arg["sql"] for arg in args),
    # Add more functions here
}


def get_sql_from_function(func_name: str, args: List[AllOutputs]) -> str:
    func = FUNCTION_SQL_MAP.get(func_name.upper())
    if not func:
        return f"UNSUPPORTED_FUNCTION({func_name})"
    return func(args)
