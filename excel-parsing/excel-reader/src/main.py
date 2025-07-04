import grpc
from clients.formula_parser import utils
from services.get_data import get_data_from_spreadsheet
from clients.formula_parser import formula_parser_pb2, formula_parser_pb2_grpc

from services import dtypes
from typing import Generator
from core.config import settings


FORMULA_PARSER_CHANNEL = grpc.insecure_channel(settings.FORMULA_PARSER_CHANNEL)
FORMULA_PARSER_STUB = formula_parser_pb2_grpc.FormulaParserStub(FORMULA_PARSER_CHANNEL)


def parse_formula(
    stub: formula_parser_pb2_grpc.FormulaParserStub, formula: str
) -> dict:
    request = formula_parser_pb2.FormulaParserRequest(formula=formula)
    response: formula_parser_pb2.FormulaParserResponse = stub.ParseFormula(request)
    return response.ast


def generate_data(
    data: dict[str, dict[str, list[dtypes.CellData]]],
) -> Generator[dict[str, str | dtypes.CellData], None, None]:
    for sheet, cols in data.items():
        for col, cells in cols.items():
            for i, cell in enumerate(cells[:1]):
                yield {
                    "sheet": sheet,
                    "col": col,
                    "cell": cell,
                    "index": i,
                }


def parse_formulas(filename: str, file_bytes: bytes):
    content = get_data_from_spreadsheet(filename, file_bytes)
    data = content["data"]
    result = {}
    for cell_data in generate_data(data):
        sheet = cell_data["sheet"]
        col = cell_data["col"]
        cell = cell_data["cell"]
        if cell["data_type"] == "s":
            cell["value"] = f'"{cell["value"]}"'

        if sheet not in result:
            result[sheet] = {}
        if col not in result[sheet]:
            result[sheet][col] = []

        cell["ast"] = parse_formula(FORMULA_PARSER_STUB, str(cell["value"]))
        result[sheet][col].append(cell)

    return result


def main(filename: str, file_bytes: bytes) -> None:
    result = parse_formulas(filename, file_bytes)
    for sheet, cols in result.items():
        for col, cells in cols.items():
            for i, cell in enumerate(cells):
                result[sheet][col][i]["ast"] = utils.parse_ast(cell["ast"])

    return result


if __name__ == "__main__":
    import json
    import os.path

    file_example = (
        "/home/juand/Documents/vscode/proyecto/etl-design/"
        "/typechecking/backend/static/acme__users__sample1.xlsx"
    )
    with open(file_example, "rb") as file:
        file_bytes = file.read()

    filename = os.path.basename(file_example)
    result = main(filename, file_bytes)
    print(json.dumps(result, indent=4, ensure_ascii=False))
