"""
Formula AST Generator - Utility to parse Excel formulas using the formula-parser CLI

This module provides a simple interface to call the TypeScript formula-parser CLI
and generate Abstract Syntax Trees (AST) from Excel formulas in English.

The formula-parser must be built before using this module:
    cd apps/backend/parsers/formula-parser
    pnpm install
    pnpm build
"""

import json
import subprocess
import sys
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List, TypedDict

from src.services.ddl_generator import generate_ddl


class FormulaParseResult(TypedDict):
    """Result structure from formula-parser CLI"""

    formula: str
    tokens: List[Dict] | None
    ast: Dict[str, Any] | None
    error: str
    success: bool


class FormulaParserError(Exception):
    """Exception raised when formula parsing fails"""

    pass


def _get_formula_parser_cli_path() -> Path:
    """
    Get the path to the formula-parser CLI script.

    Returns:
        Path: Path to the compiled CLI script (dist/cli.js)

    Raises:
        FileNotFoundError: If the formula-parser CLI is not found
    """
    # Get the ddl-generator project root
    ddl_gen_root = Path(__file__).parents[3]

    # Navigate to formula-parser
    cli_path = (
        ddl_gen_root / "formula-parser" / "dist" / "cli.cjs"
    )

    if not cli_path.exists():
        raise FileNotFoundError(
            f"Formula-parser CLI not found at {cli_path}. "
            f"Please build formula-parser first:\n"
            f"  cd {ddl_gen_root / 'formula-parser'}\n"
            f"  pnpm install && pnpm build"
        )

    return cli_path


def parse_formula(formula: str) -> FormulaParseResult:
    """
    Parse an Excel formula (in English) and generate its AST.

    Args:
        formula: Excel formula string (e.g., "=SUM(A1:A10)")

    Returns:
        FormulaParseResult: Dictionary containing:
            - formula: The input formula
            - tokens: List of tokens from tokenization
            - ast: Abstract Syntax Tree
            - error: Error message if parsing failed
            - success: Boolean indicating if parsing was successful

    Raises:
        FormulaParserError: If the formula-parser process fails
        FileNotFoundError: If the formula-parser CLI is not built
    """
    cli_path = _get_formula_parser_cli_path()

    try:
        # Execute the CLI with the formula as an argument
        result = subprocess.run(
            [sys.executable, "-m", "node", str(cli_path), formula],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Try direct node execution if python -m node fails
        if "No module named 'node'" in result.stderr or result.returncode != 0:
            result = subprocess.run(
                ["node", str(cli_path), formula],
                capture_output=True,
                text=True,
                timeout=5,
            )

        # Parse the JSON output
        try:
            output = json.loads(result.stdout)
            return FormulaParseResult(**output)
        except json.JSONDecodeError as e:
            raise FormulaParserError(
                f"Failed to parse CLI output as JSON: {result.stdout}\n"
                f"Error: {e}"
            ) from e

    except subprocess.TimeoutExpired as e:
        raise FormulaParserError(
            f"Formula parsing timed out for: {formula}"
        ) from e
    except FileNotFoundError as e:
        raise FormulaParserError(
            "Node.js not found. Please ensure Node.js is installed."
        ) from e
    except Exception as e:
        raise FormulaParserError(
            f"Unexpected error while parsing formula '{formula}': {e}"
        ) from e


def get_ast(formula: str) -> Dict[str, Any]:
    """
    Parse a formula and return only the AST.

    Convenience function for getting just the AST without other metadata.

    Args:
        formula: Excel formula string

    Returns:
        Dict: The Abstract Syntax Tree

    Raises:
        FormulaParserError: If parsing fails
    """
    result = parse_formula(formula)

    if not result["success"] or result["ast"] is None:
        raise FormulaParserError(f"Failed to parse formula: {result['error']}")

    return result["ast"]


def parse_column_mappings(mappings_str: str) -> Dict[str, str]:
    """
    Parse column mappings from a string format.

    Args:
        mappings_str: String in the format "A=col1&B=col2&..."

    Returns:
        Dict: Mapping of Excel columns to SQL column names
    """
    mappings = {}
    for pair in mappings_str.split("&"):
        if "=" in pair:
            excel_col, sql_col = pair.split("=", 1)
            mappings[excel_col.strip()] = sql_col.strip()
    return mappings


if __name__ == "__main__":
    # Simple test when run as a script
    if len(sys.argv) < 2:
        print("Usage: python formula_parser_cli.py '<formula>' '<cellName=columnName&...>'")
        print("Example: python formula_parser_cli.py '=SUM(A1:A10)'")
        sys.exit(1)

    formula = sys.argv[1]
    columns = parse_column_mappings(sys.argv[2]) if len(sys.argv) > 2 else {}
    result = parse_formula(formula)
    pprint(result)

    if result["ast"] is None or not result["success"] or len(sys.argv) <= 2:
        sys.exit(0)

    print("\nGenerated AST:")
    pprint(result["ast"])

    print("\nGenerated SQL from AST:")
    try:
        sql_result = generate_ddl({"ast": result["ast"], "columns": columns})  # type: ignore
        pprint(sql_result)
    except Exception as e:
        print(f"Error generating SQL: {e}")
