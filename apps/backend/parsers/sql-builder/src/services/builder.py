import re
from typing import Dict, List

from igraph import Graph
from proto_utils.parsers.dtypes import AllASTs, SQLResponseSQLContent

from src.services.utils import get_priority_level

PRIMARY_KEY_CLAUSE_RE = re.compile(r"\bPRIMARY\s+KEY\b", re.IGNORECASE)


def remove_primary_key_clause(extra: str) -> str:
    """Remove PRIMARY KEY from an extra clause while preserving other constraints."""
    cleaned = PRIMARY_KEY_CLAUSE_RE.sub("", extra or "")
    return " ".join(cleaned.split())


# TODO: Refactor hardcoded SQL generation
# TODO: Find a way to handle columns with formulas using "GENERATED ALWAYS AS"
# to make it less rigid for PostgreSQL usage, and find a way to make it more flexible
# so it can be used with other database engines
def build_sql(
    cols: Dict[str, AllASTs],
    dependency_graph: Graph,
    dtypes: Dict[str, Dict[str, str]],
    table_name: str,
) -> Dict[int, List[SQLResponseSQLContent]]:
    """
    Build SQL expressions from the provided column definitions and their dependencies.

    Args:
        cols (Dict[str, AllASTs]): Dictionary mapping column names to their definitions.
        dependency_graph (Graph): Dependency graph representing relationships between columns.
        dtypes (Dict[str, Dict[str, str]]): Dictionary mapping column names to their SQL data types.
        table_name (str): Name of the table to create.

    Returns:
        Dict[int, List[SQLResponseSQLContent]]: Dictionary mapping column names to their SQL expressions.
    """
    # Calculate the priority level for each column based on the dependency graph
    priorities = {
        col: get_priority_level(dependency_graph, col) for col in cols
    }
    level_0_cols = [pair[0] for pair in priorities.items() if pair[1] == 0]
    sql_expressions = {}

    # Get all primary keys
    level_0_cols_set = set(level_0_cols)
    primary_keys = [
        col
        for col, dtype in dtypes.items()
        if "primary key" in dtype.get("extra", "").lower()
        and col in level_0_cols_set
    ]

    # Create constraint for primary keys if there are any
    if len(primary_keys) > 0:
        primary_keys_str = ", ".join(primary_keys)
        primary_key_constraint = (
            f"CONSTRAINT {table_name}_pk PRIMARY KEY ({primary_keys_str})"
        )
    else:
        primary_key_constraint = ""

    # Generate SQL for level 0 columns (those without dependencies)
    columns_lvl0 = []
    columns_sql = []
    for col in level_0_cols:
        # In 'extra' we can add things like 'NOT NULL', 'UNIQUE', etc.
        extra_statements = remove_primary_key_clause(
            dtypes[col].get("extra", "")
        )
        base_sql = f"{col} {dtypes[col]['type']} {extra_statements}".strip()
        columns_lvl0.append(col)
        columns_sql.append(base_sql)

    if primary_key_constraint:
        columns_sql.append(primary_key_constraint)

    sql_level0 = (
        f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)});"
    )

    sql_expressions[0] = [
        SQLResponseSQLContent(sql=sql_level0, columns=columns_lvl0)
    ]

    # Sort based on the priority
    priorities_levels = list(set(priorities.values()))
    sql_expressions = {
        **sql_expressions,
        **{level: [] for level, _ in enumerate(priorities_levels, start=1)},
    }

    # Fill the information of the other levels
    other_levels = sorted(
        list(filter(lambda pair: pair[1] != 0, priorities.items())),
        key=lambda x: x[1],
    )

    for col, level in other_levels:
        extra_statements = remove_primary_key_clause(
            dtypes[col].get("extra", "")
        ).strip()
        sql_expression = (
            f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS "
            f"{col} {dtypes[col]['type']} {extra_statements} ".strip()
        )
        sql_expression += (
            f" GENERATED ALWAYS AS (({cols[col]['sql']})::{dtypes[col]['type']}) "
            "STORED"
        )
        sql_expressions[level].append(
            SQLResponseSQLContent(
                sql=f"{sql_expression.strip()};", columns=[col]
            )
        )

    # Remove empty levels
    items = list(sql_expressions.items())
    for level, content in items:
        if not content:
            del sql_expressions[level]

    return sql_expressions
