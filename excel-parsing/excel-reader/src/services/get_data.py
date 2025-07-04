import services.dtypes as dtypes
from services.utils import open_file_from_bytes, extract_formulas, convert_csv_to_excel


def get_data_from_spreadsheet(
    filename: str, file_bytes: bytes
) -> dtypes.SpreadsheetContent:
    """
    Main function to read an Excel file and extract formulas.

    Args:
        filename (str): The name of the spreadsheet file.
        file_bytes (bytes): The bytes of the Excel file.

    Returns:
        dtypes.SpreadsheetContent: A dictionary containing raw data, columns, and structured data
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

    cells = extract_formulas(workbook)
    columns = {
        sheet: list(map(lambda x: x[0]["value"], sheet_data.values()))
        for sheet, sheet_data in cells.items()
    }
    return {
        "raw_data": cells,
        "columns": columns,
        "data": {
            sheet: dict(
                map(
                    lambda x: (x[0], x[1][1:]), zip(columns[sheet], sheet_data.values())
                )
            )
            for sheet, sheet_data in cells.items()
        },
    }
