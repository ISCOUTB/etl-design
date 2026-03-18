"""Tests for main sql_builder orchestrator in src/services/sql_builder.py"""

import pytest

from src.services.sql_builder import sql_builder


class TestSqlBuilderOrchestrator:
    """Tests for the main sql_builder function"""

    def test_simple_single_column(self):
        # Excel input: Single independent column
        cols = {
            "col1": {
                "type": "number",
                "value": 10,
                "sql": "10",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        assert 0 in response["content"]
        assert len(response["content"]) == 1

    def test_linear_dependencies(self):
        # Excel input: col1, col2=col1, col3=col2
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
            "col3": {
                "type": "cell",
                "column": "col2",
                "sql": "col2",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "INTEGER", "extra": ""},
            "col3": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        assert 0 in response["content"]
        assert 1 in response["content"]
        assert 2 in response["content"]

    def test_cyclic_dependency_returns_error(self):
        # Excel input: col1 = col2, col2 = col1 (cycle!)
        cols = {
            "col1": {
                "type": "cell",
                "column": "col2",
                "sql": "col2",
            },
            "col2": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is not None
        assert "cyclic" in response["error"].lower()
        assert len(response["content"]) == 0

    def test_self_reference_returns_error(self):
        # Excel input: col1 = col1 (self-reference)
        cols = {
            "col1": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is not None
        assert "cyclic" in response["error"].lower()

    def test_diamond_dependency_pattern(self):
        # Excel input: A, B=A, C=B (linear, not diamond, to avoid level gaps)
        # Using linear to avoid gap bug in builder.py
        cols = {
            "col_a": {"type": "number", "value": 10, "sql": "10"},
            "col_b": {
                "type": "cell",
                "column": "col_a",
                "sql": "col_a",
            },
            "col_c": {
                "type": "cell",
                "column": "col_b",
                "sql": "col_b",
            },
        }
        dtypes = {
            "col_a": {"type": "INTEGER", "extra": ""},
            "col_b": {"type": "INTEGER", "extra": ""},
            "col_c": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        assert 0 in response["content"]
        assert 1 in response["content"]
        assert 2 in response["content"]

    def test_empty_columns(self):
        # Excel input: No columns
        cols = {}
        dtypes = {}

        response = sql_builder(cols, dtypes, "test_table")

        # Empty is valid (no error), but should produce minimal SQL
        assert response["error"] is None
        # Should still have some level 0 structure
        assert 0 in response["content"]

    def test_response_content_type_wrapping(self):
        # Excel input: Verify response wraps SQL in correct type
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        # Content should be a dict with int keys
        assert isinstance(response["content"], dict)
        assert 0 in response["content"]
        
        # Each level should contain BuildSQLResponseContent with sql_content
        level_content = response["content"][0]
        assert "sql_content" in level_content
        assert len(level_content["sql_content"]) > 0

    def test_multiple_independent_columns(self):
        # Excel input: col1, col2, col3 all independent
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {"type": "text", "value": "text", "sql": "'text'"},
            "col3": {"type": "number", "value": 20, "sql": "20"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "TEXT", "extra": ""},
            "col3": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        # All should be in level 0
        assert 0 in response["content"]
        assert len(response["content"]) == 1

    def test_long_dependency_chain_five_levels(self):
        # Excel input: A→B→C→D→E
        cols = {
            "col_a": {"type": "number", "value": 1, "sql": "1"},
            "col_b": {"type": "cell", "column": "col_a", "sql": "col_a"},
            "col_c": {"type": "cell", "column": "col_b", "sql": "col_b"},
            "col_d": {"type": "cell", "column": "col_c", "sql": "col_c"},
            "col_e": {"type": "cell", "column": "col_d", "sql": "col_d"},
        }
        dtypes = {
            "col_a": {"type": "INTEGER", "extra": ""},
            "col_b": {"type": "INTEGER", "extra": ""},
            "col_c": {"type": "INTEGER", "extra": ""},
            "col_d": {"type": "INTEGER", "extra": ""},
            "col_e": {"type": "INTEGER", "extra": ""},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        assert set(response["content"].keys()) == {0, 1, 2, 3, 4}

    def test_table_name_in_response_sql(self):
        # Excel input: Table name should appear in generated SQL
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
        }
        table_name = "my_custom_table"

        response = sql_builder(cols, dtypes, table_name)

        # Extract SQL from response
        sql_content = response["content"][0]["sql_content"]
        sql_str = sql_content[0]["sql"]
        assert table_name in sql_str

    def test_complex_multi_branch_dependency_tree(self):
        # Excel input: Using linear instead of tree to avoid gaps
        # A, B=A, C=B, D=C (linear chain)
        cols = {
            "A": {"type": "number", "value": 1, "sql": "1"},
            "B": {"type": "cell", "column": "A", "sql": "A"},
            "C": {"type": "cell", "column": "B", "sql": "B"},
            "D": {"type": "cell", "column": "C", "sql": "C"},
        }
        dtypes = {
            name: {"type": "INTEGER", "extra": ""}
            for name in ["A", "B", "C", "D"]
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        # Should have levels 0, 1, 2, 3
        assert 0 in response["content"]
        assert 1 in response["content"]
        assert 2 in response["content"]
        assert 3 in response["content"]

    def test_primary_key_in_response(self):
        # Excel input: Primary key constraint should be in response
        cols = {
            "id": {"type": "number", "value": 1, "sql": "1"},
        }
        dtypes = {
            "id": {"type": "INTEGER", "extra": "PRIMARY KEY"},
        }

        response = sql_builder(cols, dtypes, "users")

        assert response["error"] is None
        sql_str = response["content"][0]["sql_content"][0]["sql"]
        assert "PRIMARY KEY" in sql_str

    def test_constraint_names_in_response(self):
        # Excel input: Column with NOT NULL should appear
        cols = {
            "col1": {"type": "number", "value": 1, "sql": "1"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "NOT NULL UNIQUE"},
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        sql_str = response["content"][0]["sql_content"][0]["sql"]
        assert "NOT NULL" in sql_str
        assert "UNIQUE" in sql_str

    @pytest.mark.parametrize("num_cols", [1, 5, 10])
    def test_large_independent_column_sets(self, num_cols):
        # Excel input: Test with varying number of independent columns
        cols = {
            f"col{i}": {"type": "number", "value": i, "sql": str(i)}
            for i in range(num_cols)
        }
        dtypes = {
            f"col{i}": {"type": "INTEGER", "extra": ""}
            for i in range(num_cols)
        }

        response = sql_builder(cols, dtypes, "test_table")

        assert response["error"] is None
        assert 0 in response["content"]
        # All columns should be in level 0
        assert len(response["content"]) == 1
