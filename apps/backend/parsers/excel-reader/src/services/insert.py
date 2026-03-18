from typing import Dict

from src.services.get_data import get_data_from_spreadsheet


def create_sql_for_insertion(
    table_name: str, file_bytes: bytes, filename: str, truncate: bool = False
) -> Dict[str, str]:
    # The truncate parameter is dangerous and should be used with caution.
    # In this case, we will use another way instead of using TRUNCATE TABLE directly,
    # we will create a new table with the same structure and then rename it to the original table name,
    # this way we can avoid the risk of truncating the original table by mistake.

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

    n_sheets = len(non_formula_columns)
    sql_statements = {}
    for sheet, cols in non_formula_columns.items():
        table_name_sheet = (
            f"{table_name}_{sheet}" if n_sheets > 1 else table_name
        )
        table_name_sheet_tmp = f"{table_name_sheet}_temp"

        prefix_sql = ""
        if truncate:
            # Create temporal table
            prefix_sql += f"CREATE TABLE {table_name_sheet_tmp} (LIKE {table_name_sheet} INCLUDING ALL);\n"

            # Insert data into temporal table

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

        insert_sql = f"INSERT INTO {table_name_sheet} ({column_list}) VALUES {values_list};"

        suffix_sql = ""
        if truncate:
            # Rename temporal table to original table name
            # We will do it atomically

            # Create a transaction to ensure atomicity
            suffix_sql += "\nBEGIN;\n"

            # Rename original table to backup, and the new table to original name
            suffix_sql += f"ALTER TABLE {table_name_sheet} RENAME TO {table_name_sheet}_backup;\n"
            suffix_sql += f"ALTER TABLE {table_name_sheet_tmp} RENAME TO {table_name_sheet};\n"

            # I'll drop the backup table here, but maybe we will use something like TTLs
            # (postgres don't support it natively but we can create a background job to drop backup
            # tables older than X days) to keep some backups just in case
            suffix_sql += f"DROP TABLE {table_name_sheet}_backup;\n"

            # Commit the transaction
            suffix_sql += "COMMIT;"

        sql_statements[sheet] = f"{prefix_sql}{insert_sql}{suffix_sql}"

    return sql_statements
