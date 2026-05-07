from typing import Dict, Optional

from proto_utils.parsers.dtypes import (
    AllASTs,
    BuildSQLResponse,
    BuildSQLResponseContent,
)

from src.services.builder import build_sql
from src.services.create_graph import create_dependency_graph
from src.services.utils import has_cyclic_dependencies


def sql_builder(
    cols: Dict[str, AllASTs],
    dtypes: Dict[str, Dict[str, str]],
    table_name: str,
    scheme: Optional[str] = None,
) -> BuildSQLResponse:
    """
    Main function to build SQL expressions from column definitions and their dependencies.

    Args:
        cols (Dict[str, AllASTs]): Column definitions with their types and SQL expressions.
        dtypes (Dict[str, Dict[str, str]]): Data types for each column.
        table_name (str): Name of the table to create.

    Returns:
        dtypes.BuildSQLResponse: Dictionary mapping column names to their SQL expressions.
    """
    graph = create_dependency_graph(cols)
    if has_cyclic_dependencies(graph):
        return BuildSQLResponse(
            content={},
            error="The AST contains cyclic dependencies.",
        )

    sql_expressions = build_sql(cols, graph, dtypes, table_name, scheme)
    sql_expressions = dict(
        map(
            lambda item: (
                int(item[0]),
                BuildSQLResponseContent(sql_content=item[1]),
            ),
            sql_expressions.items(),
        )
    )

    # Just in case
    # sql_expressions = {
    #     level: [transpile(expr, read="postgres")[0] for expr in expressions]
    #     for level, expressions in sql_expressions.items()
    # }
    return BuildSQLResponse(content=sql_expressions, error=None)
