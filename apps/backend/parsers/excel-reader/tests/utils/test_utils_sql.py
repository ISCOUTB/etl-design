from src.schemas import (
    DtypesEnum,
    IntegerConstraints,
    SpreadsheetDtypesSchema,
    StringConstraints,
)
from src.utils.sql import generate_extra_statements_sql, get_column_type_sql


def test_generate_extra_statements_sql_numeric_constraints():
    col = SpreadsheetDtypesSchema(
        dtype=DtypesEnum.INTEGER,
        primary_key=True,
        unique=True,
        optional=False,
        constraints=IntegerConstraints(
            minimum=0,
            maximum=10,
            exclusive_minimum=True,
            exclusive_maximum=False,
            multiple_of=2,
        ),
    )

    sql = generate_extra_statements_sql("age", col)

    assert "PRIMARY KEY" in sql
    assert "UNIQUE" in sql
    assert "NOT NULL" in sql
    assert "CHECK (age > 0)" in sql
    assert "CHECK (age <= 10)" in sql
    assert "CHECK (MOD(age, 2) = 0)" in sql


def test_generate_extra_statements_sql_string_constraints():
    col = SpreadsheetDtypesSchema(
        dtype=DtypesEnum.STRING,
        optional=True,
        constraints=StringConstraints(
            min_length=3,
            max_length=10,
            pattern="^[a-z]+$",
        ),
    )

    sql = generate_extra_statements_sql("name", col)

    assert "CHECK (LENGTH(name) >= 3)" in sql
    assert "CHECK (LENGTH(name) <= 10)" in sql
    assert "CHECK (name ~ '^[a-z]+$')" in sql


def test_generate_extra_statements_sql_without_constraints():
    col = SpreadsheetDtypesSchema(dtype=DtypesEnum.BOOLEAN)

    sql = generate_extra_statements_sql("active", col)

    assert sql == ""


def test_get_column_type_sql_mappings():
    assert (
        get_column_type_sql(SpreadsheetDtypesSchema(dtype=DtypesEnum.INTEGER))
        == "INTEGER"
    )
    assert (
        get_column_type_sql(SpreadsheetDtypesSchema(dtype=DtypesEnum.FLOAT))
        == "REAL"
    )
    assert (
        get_column_type_sql(SpreadsheetDtypesSchema(dtype=DtypesEnum.DOUBLE))
        == "DOUBLE PRECISION"
    )
    assert (
        get_column_type_sql(SpreadsheetDtypesSchema(dtype=DtypesEnum.BOOLEAN))
        == "BOOLEAN"
    )


def test_get_column_type_sql_string_max_length_to_varchar():
    col = SpreadsheetDtypesSchema(
        dtype=DtypesEnum.STRING,
        constraints=StringConstraints(max_length=120),
    )

    assert get_column_type_sql(col) == "VARCHAR(120)"


def test_get_column_type_sql_string_without_max_length_is_text():
    col = SpreadsheetDtypesSchema(
        dtype=DtypesEnum.STRING,
        constraints=StringConstraints(min_length=2),
    )

    assert get_column_type_sql(col) == "TEXT"
