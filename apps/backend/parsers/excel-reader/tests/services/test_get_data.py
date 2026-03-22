import pytest

from src.services.get_data import get_data_from_spreadsheet


def test_get_data_from_spreadsheet_uses_open_file_for_xlsx(monkeypatch):
    fake_workbook = object()

    monkeypatch.setattr(
        "src.services.get_data.open_file_from_bytes",
        lambda _bytes: fake_workbook,
    )
    monkeypatch.setattr(
        "src.services.get_data.extract_cell_data",
        lambda _wb, _limit: {
            "Sheet1": {
                "A": [
                    {
                        "cell": "A1",
                        "value": "full name",
                        "data_type": "s",
                        "is_formula": False,
                    },
                    {
                        "cell": "A2",
                        "value": "Alice",
                        "data_type": "s",
                        "is_formula": False,
                    },
                ]
            }
        },
    )

    result = get_data_from_spreadsheet(
        filename="users.xlsx",
        file_bytes=b"binary",
        limit=10,
        fill_spaces="_",
    )

    assert result["columns"]["Sheet1"]["A"]["name"] == "full_name"
    assert result["columns"]["Sheet1"]["A"]["is_formula"] is False
    assert result["data"]["Sheet1"]["A"][0]["value"] == "Alice"


def test_get_data_from_spreadsheet_uses_csv_converter(monkeypatch):
    fake_workbook = object()

    monkeypatch.setattr(
        "src.services.get_data.convert_csv_to_excel",
        lambda _bytes: fake_workbook,
    )
    monkeypatch.setattr(
        "src.services.get_data.extract_cell_data",
        lambda _wb, _limit: {
            "Sheet1": {
                "A": [
                    {
                        "cell": "A1",
                        "value": "id",
                        "data_type": "s",
                        "is_formula": False,
                    },
                    {
                        "cell": "A2",
                        "value": "1",
                        "data_type": "s",
                        "is_formula": False,
                    },
                ]
            }
        },
    )

    result = get_data_from_spreadsheet(
        filename="users.csv",
        file_bytes=b"id\n1",
    )

    assert result["columns"]["Sheet1"]["A"]["name"] == "id"


def test_get_data_from_spreadsheet_unsupported_extension_raises():
    with pytest.raises(NotImplementedError, match="Unsupported file format"):
        get_data_from_spreadsheet(
            filename="users.txt",
            file_bytes=b"plain text",
        )


def test_get_data_from_spreadsheet_empty_fill_spaces_defaults_to_space(
    monkeypatch,
):
    monkeypatch.setattr(
        "src.services.get_data.open_file_from_bytes",
        lambda _bytes: object(),
    )
    monkeypatch.setattr(
        "src.services.get_data.extract_cell_data",
        lambda _wb, _limit: {
            "Sheet1": {
                "A": [
                    {
                        "cell": "A1",
                        "value": "full name",
                        "data_type": "s",
                        "is_formula": False,
                    },
                    {
                        "cell": "A2",
                        "value": "Alice",
                        "data_type": "s",
                        "is_formula": False,
                    },
                ]
            }
        },
    )

    result = get_data_from_spreadsheet(
        filename="users.xlsx",
        file_bytes=b"binary",
        fill_spaces="",
    )

    # With empty fill_spaces, it should keep a normal space.
    assert result["columns"]["Sheet1"]["A"]["name"] == "full_name"
