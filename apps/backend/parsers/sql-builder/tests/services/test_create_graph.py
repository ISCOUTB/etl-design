"""Tests for dependency graph creation in src/services/create_graph.py"""

import pytest

from src.services.create_graph import create_dependency_graph


class TestCreateDependencyGraph:
    """Tests for create_dependency_graph function"""

    def test_single_independent_column(self):
        # Excel input: Single number column without dependencies
        cols = {
            "col1": {"type": "number", "value": 10},
        }
        
        graph = create_dependency_graph(cols)
        
        assert "col1" in graph.vs["name"]
        assert len(graph.es) == 0  # No edges

    def test_multiple_independent_columns(self):
        # Excel input: Multiple columns, all just numbers
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {"type": "number", "value": 20},
            "col3": {"type": "text", "value": "hello"},
        }
        
        graph = create_dependency_graph(cols)
        
        assert set(graph.vs["name"]) == {"col1", "col2", "col3"}
        assert len(graph.es) == 0  # No edges

    def test_single_cell_reference(self):
        # Excel input: col2 = col1 (cell reference)
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {
                "type": "cell",
                "cell": "A2",
                "refType": "relative",
                "column": "col1",
                "error": None,
                "sql": "col1",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        assert set(graph.vs["name"]) == {"col1", "col2"}
        # col2 depends on col1, so edge col2→col1
        edges = [(e.source, e.target) for e in graph.es]
        assert ("col2", "col1") in [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in edges
        ]

    def test_cell_range_reference(self):
        # Excel input: col4 = SUM(col1:col3)
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {"type": "number", "value": 20},
            "col3": {"type": "number", "value": 30},
            "col4": {
                "type": "cell_range",
                "range": "A1:C1",
                "refType": "relative",
                "columns": ["col1", "col2", "col3"],
                "error": None,
                "sql": "(col1 + col2 + col3)",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert ("col4", "col1") in edges_names
        assert ("col4", "col2") in edges_names
        assert ("col4", "col3") in edges_names
        assert len(edges_names) == 3

    def test_binary_expression(self):
        # Excel input: col3 = col1 + col2
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {"type": "number", "value": 20},
            "col3": {
                "type": "binary-expression",
                "operator": "+",
                "left": {
                    "type": "cell",
                    "cell": "A1",
                    "column": "col1",
                    "sql": "col1",
                },
                "right": {
                    "type": "cell",
                    "cell": "B1",
                    "column": "col2",
                    "sql": "col2",
                },
                "sql": "(col1) + (col2)",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert ("col3", "col1") in edges_names
        assert ("col3", "col2") in edges_names

    def test_unary_expression(self):
        # Excel input: col2 = -col1
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {
                "type": "unary-expression",
                "operator": "-",
                "operand": {
                    "type": "cell",
                    "cell": "A1",
                    "column": "col1",
                    "sql": "col1",
                },
                "sql": "-(col1)",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert ("col2", "col1") in edges_names
        assert len(edges_names) == 1

    def test_function_with_cell_arguments(self):
        # Excel input: col4 = IF(col1 > col2, col3, 0)
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {"type": "number", "value": 5},
            "col3": {"type": "number", "value": 100},
            "col4": {
                "type": "function",
                "name": "IF",
                "arguments": [
                    {
                        "type": "binary-expression",
                        "operator": ">",
                        "left": {
                            "type": "cell",
                            "column": "col1",
                            "sql": "col1",
                        },
                        "right": {
                            "type": "cell",
                            "column": "col2",
                            "sql": "col2",
                        },
                        "sql": "(col1) > (col2)",
                    },
                    {
                        "type": "cell",
                        "column": "col3",
                        "sql": "col3",
                    },
                    {"type": "number", "value": 0},
                ],
                "sql": "CASE WHEN (col1) > (col2) THEN col3 ELSE 0 END",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        # col4 should depend on col1, col2, col3
        assert ("col4", "col1") in edges_names
        assert ("col4", "col2") in edges_names
        assert ("col4", "col3") in edges_names
        assert len(edges_names) == 3

    def test_linear_chain_dependencies(self):
        # Excel input: col1, col2=col1, col3=col2
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {
                "type": "cell",
                "cell": "A1",
                "column": "col1",
                "sql": "col1",
            },
            "col3": {
                "type": "cell",
                "cell": "B1",
                "column": "col2",
                "sql": "col2",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert ("col2", "col1") in edges_names
        assert ("col3", "col2") in edges_names
        assert len(edges_names) == 2

    def test_diamond_pattern_dependencies(self):
        # Excel input: A, B=A, C=A, D=B+C
        cols = {
            "col_a": {"type": "number", "value": 10},
            "col_b": {
                "type": "cell",
                "column": "col_a",
                "sql": "col_a",
            },
            "col_c": {
                "type": "cell",
                "column": "col_a",
                "sql": "col_a",
            },
            "col_d": {
                "type": "binary-expression",
                "operator": "+",
                "left": {
                    "type": "cell",
                    "column": "col_b",
                    "sql": "col_b",
                },
                "right": {
                    "type": "cell",
                    "column": "col_c",
                    "sql": "col_c",
                },
                "sql": "(col_b) + (col_c)",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert ("col_b", "col_a") in edges_names
        assert ("col_c", "col_a") in edges_names
        assert ("col_d", "col_b") in edges_names
        assert ("col_d", "col_c") in edges_names

    def test_constant_function_no_cell_references(self):
        # Excel input: col2 = IF(TRUE, 10, 20) - no cell references
        cols = {
            "col1": {"type": "number", "value": 5},
            "col2": {
                "type": "function",
                "name": "IF",
                "arguments": [
                    {"type": "logical", "value": True},
                    {"type": "number", "value": 10},
                    {"type": "number", "value": 20},
                ],
                "sql": "CASE WHEN TRUE THEN 10 ELSE 20 END",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        # col2 has no cell references, so no edge
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        assert len(edges_names) == 0

    def test_empty_columns(self):
        # Excel input: Empty columns dict
        cols = {}
        
        graph = create_dependency_graph(cols)
        
        assert len(graph.vs) == 0
        assert len(graph.es) == 0

    def test_complex_nested_expression(self):
        # Excel input: col4 = (col1 + col2) * (col3 - 1)
        cols = {
            "col1": {"type": "number", "value": 10},
            "col2": {"type": "number", "value": 20},
            "col3": {"type": "number", "value": 30},
            "col4": {
                "type": "binary-expression",
                "operator": "*",
                "left": {
                    "type": "binary-expression",
                    "operator": "+",
                    "left": {
                        "type": "cell",
                        "column": "col1",
                        "sql": "col1",
                    },
                    "right": {
                        "type": "cell",
                        "column": "col2",
                        "sql": "col2",
                    },
                    "sql": "(col1) + (col2)",
                },
                "right": {
                    "type": "binary-expression",
                    "operator": "-",
                    "left": {
                        "type": "cell",
                        "column": "col3",
                        "sql": "col3",
                    },
                    "right": {"type": "number", "value": 1},
                    "sql": "(col3) - (1)",
                },
                "sql": "((col1) + (col2)) * ((col3) - (1))",
            },
        }
        
        graph = create_dependency_graph(cols)
        
        edges_names = [
            (graph.vs[s]["name"], graph.vs[t]["name"]) for s, t in [(e.source, e.target) for e in graph.es]
        ]
        # col4 should depend on col1, col2, col3
        assert ("col4", "col1") in edges_names
        assert ("col4", "col2") in edges_names
        assert ("col4", "col3") in edges_names
        assert len(edges_names) == 3
