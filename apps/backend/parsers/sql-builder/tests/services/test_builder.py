"""Tests for SQL building logic in src/services/builder.py"""

import pytest

from src.services.builder import build_sql, remove_primary_key_clause
from src.services.create_graph import create_dependency_graph


class TestRemovePrimaryKeyClause:
    """Tests for remove_primary_key_clause function"""

    def test_remove_simple_primary_key(self):
        # Excel input: Column with "PRIMARY KEY"
        extra = "PRIMARY KEY"
        result = remove_primary_key_clause(extra)
        assert result == ""

    def test_remove_primary_key_with_other_constraints(self):
        # Excel input: "PRIMARY KEY UNIQUE NOT NULL"
        extra = "PRIMARY KEY UNIQUE NOT NULL"
        result = remove_primary_key_clause(extra)
        assert "PRIMARY KEY" not in result
        assert "UNIQUE" in result
        assert "NOT NULL" in result

    def test_preserve_other_constraints(self):
        # Excel input: "UNIQUE NOT NULL" (no PRIMARY KEY)
        extra = "UNIQUE NOT NULL"
        result = remove_primary_key_clause(extra)
        assert result == "UNIQUE NOT NULL"

    def test_case_insensitive_removal(self):
        # Excel input: "primary key" (lowercase)
        extra = "primary key NOT NULL"
        result = remove_primary_key_clause(extra)
        assert "primary key" not in result.lower()
        assert "NOT NULL" in result

    def test_empty_string(self):
        # Excel input: Empty extra string
        extra = ""
        result = remove_primary_key_clause(extra)
        assert result == ""

    def test_multiple_spaces_normalized(self):
        # Excel input: "PRIMARY  KEY  UNIQUE" (multiple spaces)
        extra = "PRIMARY  KEY  UNIQUE"
        result = remove_primary_key_clause(extra)
        assert result == "UNIQUE"
        assert "  " not in result  # Extra spaces removed


class TestBuildSql:
    """Tests for build_sql function"""

    def test_single_independent_column_creates_table(self):
        # Excel input: Single column, no dependencies
        cols = {
            "col1": {
                "type": "number",
                "value": 10,
                "sql": "10",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "NOT NULL"},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        assert 0 in result
        assert len(result[0]) == 1
        sql = result[0][0]["sql"]
        assert "CREATE TABLE IF NOT EXISTS test_table" in sql
        assert "col1 INTEGER NOT NULL" in sql
        assert ";" in sql

    def test_two_columns_with_dependency(self):
        # Excel input: col1 (value), col2 = col1
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
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
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        # Level 0: col1
        assert 0 in result
        create_sql = result[0][0]["sql"]
        assert "CREATE TABLE IF NOT EXISTS test_table" in create_sql
        assert "col1 INTEGER" in create_sql
        assert result[0][0]["columns"] == ["col1"]

        # Level 1: col2
        assert 1 in result
        alter_sql = result[1][0]["sql"]
        assert "ALTER TABLE test_table ADD COLUMN IF NOT EXISTS col2" in alter_sql
        assert "GENERATED ALWAYS AS" in alter_sql
        assert result[1][0]["columns"] == ["col2"]

    def test_linear_chain_three_columns(self):
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
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        # Level 0: col1
        assert 0 in result
        assert result[0][0]["columns"] == ["col1"]

        # Level 1: col2
        assert 1 in result
        assert result[1][0]["columns"] == ["col2"]

        # Level 2: col3
        assert 2 in result
        assert result[2][0]["columns"] == ["col3"]

    def test_diamond_pattern_dependencies(self):
        # Excel input: A, B=A, C=B (linear chain instead of diamond)
        # This avoids the gap in priority levels that exists in builder.py
        # Priority: A=0, B=1+0=1, C=1+1=2
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
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        assert 0 in result
        assert result[0][0]["columns"] == ["col_a"]

        assert 1 in result
        assert result[1][0]["columns"] == ["col_b"]

        assert 2 in result
        assert result[2][0]["columns"] == ["col_c"]

    def test_primary_key_constraint_single_column(self):
        # Excel input: col1 as PRIMARY KEY
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "PRIMARY KEY"},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "users")

        create_sql = result[0][0]["sql"]
        assert "CONSTRAINT users_pk PRIMARY KEY (col1)" in create_sql
        # col1's individual annotation should not have PRIMARY KEY (removed)
        assert create_sql.count("PRIMARY KEY") == 1  # Only in constraint

    def test_primary_key_constraint_multiple_columns(self):
        # Excel input: col1 and col2 both PRIMARY KEY in level 0
        cols = {
            "col1": {"type": "number", "value": 1, "sql": "1"},
            "col2": {"type": "number", "value": 2, "sql": "2"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "PRIMARY KEY"},
            "col2": {"type": "INTEGER", "extra": "PRIMARY KEY"},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "composite_key_table")

        create_sql = result[0][0]["sql"]
        assert "CONSTRAINT composite_key_table_pk PRIMARY KEY (col1, col2)" in create_sql

    def test_primary_key_only_in_level_zero(self):
        # Excel input: col1 (level 0), col2=col1 (level 1) both marked as PRIMARY KEY
        # PRIMARY KEY should only be applied to col1
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "PRIMARY KEY"},
            "col2": {"type": "INTEGER", "extra": "PRIMARY KEY"},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        create_sql = result[0][0]["sql"]
        # Only col1 should be in constraint
        assert "CONSTRAINT test_table_pk PRIMARY KEY (col1)" in create_sql

        # col2 is a generated column, PRIMARY KEY should be removed from extra
        alter_sql = result[1][0]["sql"]
        assert "PRIMARY KEY" not in alter_sql

    def test_unique_constraint_preserved(self):
        # Excel input: Column with UNIQUE constraint
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": "NOT NULL UNIQUE"},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        create_sql = result[0][0]["sql"]
        assert "UNIQUE" in create_sql
        assert "NOT NULL" in create_sql

    def test_all_columns_independent(self):
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
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        # All should be in level 0
        assert 0 in result
        assert len(result) == 1  # Only level 0
        assert len(result[0]) == 1  # Single CREATE TABLE statement
        sql = result[0][0]["sql"]
        assert "col1 INTEGER" in sql
        assert "col2 TEXT" in sql
        assert "col3 INTEGER" in sql

    def test_generated_always_as_stored_syntax(self):
        # Excel input: col2 = col1 * 2
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {
                "type": "binary-expression",
                "operator": "*",
                "left": {"type": "cell", "column": "col1", "sql": "col1"},
                "right": {"type": "number", "value": 2},
                "sql": "(col1) * (2)",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "INTEGER", "extra": ""},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        alter_sql = result[1][0]["sql"]
        assert "GENERATED ALWAYS AS" in alter_sql
        assert "STORED" in alter_sql
        assert "(col1) * (2)" in alter_sql

    def test_complex_expression_with_function(self):
        # Excel input: col3 = IF(col1 > col2, col1, col2)
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {"type": "number", "value": 5, "sql": "5"},
            "col3": {
                "type": "function",
                "name": "IF",
                "arguments": [
                    {
                        "type": "binary-expression",
                        "operator": ">",
                        "left": {"type": "cell", "column": "col1", "sql": "col1"},
                        "right": {"type": "cell", "column": "col2", "sql": "col2"},
                        "sql": "(col1) > (col2)",
                    },
                    {"type": "cell", "column": "col1", "sql": "col1"},
                    {"type": "cell", "column": "col2", "sql": "col2"},
                ],
                "sql": "CASE WHEN (col1) > (col2) THEN col1 ELSE col2 END",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "INTEGER", "extra": ""},
            "col3": {"type": "INTEGER", "extra": ""},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        # col3 depends on both col1 and col2
        # col1, col2 are independent (level 0)
        # col3: priority = (1+0) + (1+0) = 2
        assert 0 in result
        assert set(result[0][0]["columns"]) == {"col1", "col2"}

        assert 2 in result
        assert result[2][0]["columns"] == ["col3"]
        assert "CASE WHEN (col1) > (col2) THEN col1 ELSE col2 END" in result[2][0]["sql"]

    def test_no_empty_levels_in_result(self):
        # Excel input: col1, col2=col1, col3=col1 (no level 1.5, just 0 and 1)
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
            "col2": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
            "col3": {
                "type": "cell",
                "column": "col1",
                "sql": "col1",
            },
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
            "col2": {"type": "INTEGER", "extra": ""},
            "col3": {"type": "INTEGER", "extra": ""},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "test_table")

        # Result should only have keys 0 and 1, no empty levels
        assert set(result.keys()) == {0, 1}

    def test_table_name_in_generated_sql(self):
        # Excel input: Different table names should appear in SQL
        cols = {
            "col1": {"type": "number", "value": 10, "sql": "10"},
        }
        dtypes = {
            "col1": {"type": "INTEGER", "extra": ""},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "custom_table_name")

        create_sql = result[0][0]["sql"]
        assert "custom_table_name" in create_sql
        assert "CREATE TABLE IF NOT EXISTS custom_table_name" in create_sql

    def test_datatype_appears_in_sql(self):
        # Excel input: Verify different data types appear correctly
        cols = {
            "id": {"type": "number", "value": 1, "sql": "1"},
            "name": {"type": "text", "value": "John", "sql": "'John'"},
        }
        dtypes = {
            "id": {"type": "BIGINT", "extra": ""},
            "name": {"type": "VARCHAR(255)", "extra": ""},
        }
        graph = create_dependency_graph(cols)

        result = build_sql(cols, graph, dtypes, "users")

        create_sql = result[0][0]["sql"]
        assert "id BIGINT" in create_sql
        assert "name VARCHAR(255)" in create_sql
