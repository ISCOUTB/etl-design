import dtypes
from typing import Dict

from create_graph import create_dependency_graph
from builder import build_sql


def main(
    cols: Dict[str, dtypes.AllOutputs],
    dtypes: Dict[str, str],
    table_name: str,
) -> str:
    """
    Main function to build SQL expressions from column definitions and their dependencies.

    Args:
        cols (Dict[str, dtypes.AllOutputs]): Column definitions with their types and SQL expressions.
        dtypes (Dict[str, str]): Data types for each column.
        table_name (str): Name of the table to create.

    Returns:
        str: SQL expressions for creating the table and adding generated columns.
    """
    graph = create_dependency_graph(cols)
    sql_expressions = build_sql(cols, graph, dtypes, table_name)
    sql_expression = f"{sql_expressions[0]}\n"  # Start with the CREATE TABLE statement
    for level, expressions in sql_expressions.items():
        if level == 0:
            continue
        for expr in expressions:
            sql_expression += f"\n{expr}"

    return sql_expression


if __name__ == "__main__":
    cols: Dict[str, dtypes.AllOutputs] = {
        "col1": {"type": "number", "value": 10},
        "col2": {
            "type": "function",
            "arguments": [
                {
                    "type": "binary-expression",
                    "operator": ">",
                    "left": {
                        "type": "cell",
                        "cell": "A1",
                        "refType": "relative",
                        "column": "col1",
                        "error": None,
                        "sql": "col1",
                    },
                    "right": {"type": "number", "value": 18.0, "sql": 18},
                    "sql": "(col1) > (18)",
                },
                {"type": "text", "value": "Adult", "sql": "'Adult'"},
                {"type": "text", "value": "Minor", "sql": "'Minor'"},
            ],
            "name": "IF",
            "sql": "CASE WHEN (col1) > (18) THEN 'Adult' ELSE 'Minor' END",
        },
        "col3": {
            "type": "cell",
            "cell": "B1",
            "refType": "relative",
            "column": "col2",
            "error": None,
            "sql": "col2",
        },
        "col4": {"type": "number", "value": 10},
    }

    print(
        main(
            cols,
            table_name="test_table",
            dtypes={
                "col1": {"type": "INTEGER"},
                "col2": {"type": "TEXT"},
                "col3": {"type": "TEXT"},
                "col4": {"type": "INTEGER"},
            },
        )
    )
