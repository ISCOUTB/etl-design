import logging
from typing import Optional

from src import schemas
from src.services.utils import (
    convert_csv_to_excel,
    extract_cell_data,
    open_file_from_bytes,
)
from src.utils.formatting import standardize_string
from src.utils.monitor_performance import monitor_performance

logging.basicConfig(level=logging.INFO)


@monitor_performance("get_data_from_spreadsheet")
def get_data_from_spreadsheet(
    filename: str,
    file_bytes: bytes,
    limit: Optional[int] = None,
    fill_spaces: str = " ",
) -> schemas.SpreadsheetContent:
    """
    Main function to read an Excel file and extract formulas.

    Args:
        filename (str): The name of the spreadsheet file.
        file_bytes (bytes): The bytes of the Excel file.
        limit (int): The maximum number of cells to extract per column.
        fill_spaces (str): The character to replace spaces in column names.

    Returns:
        schemas.SpreadsheetContent: A dictionary containing raw data, columns, and structured data
        extracted from the spreadsheet file.
    """

    if filename.endswith((".xlsx", ".xls")):
        workbook = open_file_from_bytes(file_bytes)
    elif filename.endswith(".csv"):
        workbook = convert_csv_to_excel(file_bytes)
    else:
        raise NotImplementedError(
            "Unsupported file format. Only .xlsx, .xls, and .csv are supported."
        )

    if not fill_spaces:
        fill_spaces = " "

    cells = extract_cell_data(workbook, limit)
    columns = {
        sheet: dict(
            map(
                # Use first cell as column name, and, MAYBE, replace spaces with underscores
                # to avoid issues with column names in SQL, but this validation maybe
                # have to be done in the client side, not here, because of dtypes_str
                # parameter received in the server, there could be a conflict with the column names
                lambda x: (
                    x[0],
                    schemas.ColumnMetadata(
                        name=standardize_string(
                            str(x[1][0]["value"]),
                            fill_spaces=fill_spaces,
                        ),
                        is_formula=any(cell["is_formula"] for cell in x[1][1:]),
                    ),
                ),
                sheet_data.items(),
            )
        )
        for sheet, sheet_data in cells.items()
    }
    return {
        "raw_data": cells,
        "columns": columns,
        "data": {
            sheet: dict(
                map(
                    lambda x: (x[0], x[1][1:]),
                    zip(columns[sheet], sheet_data.values()),
                )
            )
            for sheet, sheet_data in cells.items()
        },
    }
