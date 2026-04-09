from src.schemas import (
    DtypesEnum,
    NumberConstraints,
    SpreadsheetDtypesSchema,
    StringConstraints,
)


def generate_extra_statements_sql(
    colname: str, col: SpreadsheetDtypesSchema
) -> str:
    statements = []

    if col.primary_key:
        statements.append("PRIMARY KEY")

    if col.unique:
        statements.append("UNIQUE")

    if not col.optional:
        statements.append("NOT NULL")

    if col.constraints:
        constraint = col.constraints
        if isinstance(constraint, NumberConstraints):
            if constraint.minimum is not None:
                operator = ">" if constraint.exclusive_minimum else ">="
                statements.append(
                    f"CHECK ({colname} {operator} {constraint.minimum})"
                )
            if constraint.maximum is not None:
                operator = "<" if constraint.exclusive_maximum else "<="
                statements.append(
                    f"CHECK ({colname} {operator} {constraint.maximum})"
                )
            if constraint.multiple_of is not None:
                statements.append(
                    f"CHECK (MOD({colname}, {constraint.multiple_of}) = 0)"
                )

        if isinstance(constraint, StringConstraints):
            if constraint.min_length is not None:
                statements.append(
                    f"CHECK (LENGTH({colname}) >= {constraint.min_length})"
                )
            if constraint.max_length is not None:
                statements.append(
                    f"CHECK (LENGTH({colname}) <= {constraint.max_length})"
                )
            if constraint.pattern is not None:
                statements.append(f"CHECK ({colname} ~ '{constraint.pattern}')")

    return " ".join(statements)


def get_column_type_sql(col: SpreadsheetDtypesSchema) -> str:
    postgresql_mapping_types = {
        DtypesEnum.INTEGER: "INTEGER",
        DtypesEnum.FLOAT: "REAL",
        DtypesEnum.DOUBLE: "DOUBLE PRECISION",
        DtypesEnum.STRING: "TEXT",
        DtypesEnum.BOOLEAN: "BOOLEAN",
    }

    sql_type = postgresql_mapping_types.get(col.dtype, "TEXT")
    if (
        sql_type == "TEXT"
        and col.constraints
        and isinstance(col.constraints, StringConstraints)
    ):
        if col.constraints.max_length is not None:
            sql_type = f"VARCHAR({col.constraints.max_length})"

    return sql_type


if __name__ == "__main__":
    from src.schemas import (  # noqa: F401
        DtypesEnum,
        FloatConstraints,
        IntegerConstraints,
    )

    # Example usage
    col_schema = SpreadsheetDtypesSchema(
        dtype=DtypesEnum.INTEGER,
        unique=True,
        optional=False,
        primary_key=False,
        constraints=IntegerConstraints(
            minimum=0, maximum=100, exclusive_minimum=True
        ),
    )

    sql_statements = generate_extra_statements_sql("age", col_schema)
    print(sql_statements)
