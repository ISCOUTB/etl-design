"""Unit tests for string formatting utilities."""

import pytest

from src.utils.formatting import _normalize_fill_spaces, standardize_string


class TestNormalizeFillSpaces:
    @pytest.mark.parametrize(
        "fill_spaces,expected",
        [
            ("", ""),
            ("_", "_"),
            ("-", "_"),
            (" Á-B ", "ab"),
            ("___", "___"),
        ],
    )
    def test_normalize_fill_spaces(self, fill_spaces, expected):
        assert _normalize_fill_spaces(fill_spaces) == expected


class TestStandardizeString:
    @pytest.mark.parametrize(
        "value,fill_spaces,expected",
        [
            ("  Némotécnico Precio  ", "_", "nemotecnico_precio"),
            ("A B", "", "ab"),
            ("A B", "-", "a_b"),
            ("A   B", "__", "a_b"),
            ("col$%#1", "_", "col1"),
            ("__A   B__", "_", "a_b"),
            ("123abc", "_", "_123abc"),
            (42, "_", "_42"),
        ],
    )
    def test_standardize_string_common_cases(self, value, fill_spaces, expected):
        assert standardize_string(value, fill_spaces=fill_spaces) == expected

    @pytest.mark.parametrize("value", ["", "   ", "!!!", "___"])
    def test_standardize_string_returns_unnamed_when_empty_after_normalization(
        self, value
    ):
        assert standardize_string(value) == "unnamed"
