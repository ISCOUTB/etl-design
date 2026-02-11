from typing import Dict

from src.services.get_data import get_data_from_spreadsheet


def create_sql_for_insertion(
    table_name: str, file_bytes: bytes, filename: str
) -> Dict[str, str]:
    content = get_data_from_spreadsheet(
        file_bytes=file_bytes, filename=filename, limit=None
    )
    columns = content["columns"]
    data = content["data"]

    non_formula_columns = {
        sheet: {
            col: meta
            for col, meta in letter_info.items()
            if not meta["is_formula"]
        }
        for sheet, letter_info in columns.items()
    }

    sql_statements = {}
    for sheet, cols in non_formula_columns.items():
        column_names = [meta["name"] for meta in cols.values()]
        column_list = ", ".join(column_names)
        sheet_data = data[sheet]
        values = [[]]

        print(values)
        for col_letter in cols.keys():
            col_data = sheet_data[col_letter]
            for row_i, cell in enumerate(col_data):
                cell_value = cell["value"]
                if isinstance(cell_value, str):
                    cell_value = f"'{cell_value}'"
                if cell_value is None:
                    cell_value = "NULL"

                if row_i >= len(values):
                    values.append([])

                values[row_i].append(cell_value)

        values_list = ", ".join(
            f"({', '.join(map(str, row_values))})" for row_values in values
        )
        sql_statements[sheet] = (
            f"INSERT INTO {table_name}_{sheet} ({column_list}) VALUES {values_list};"
        )

    return sql_statements
