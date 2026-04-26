import re

from src.models import UserRole


def get_import_name(project_id: str, table_name: str) -> str:
    return f"{project_id}__{table_name}"


def table_name_from_create_sql_response(sql_response: str) -> str:
    # Extract the table name from the CREATE TABLE SQL statement
    # This is a simple regex that assumes the format "CREATE TABLE table_name ( ... )"
    if not sql_response:
        raise ValueError("SQL response is empty")

    start_pattern = r"CREATE TABLE\s+(\w+)"
    if sql_response.strip().upper().startswith("CREATE TABLE IF NOT EXISTS"):
        start_pattern = r"CREATE TABLE IF NOT EXISTS\s+(\w+)"

    match = re.search(start_pattern, sql_response, re.IGNORECASE)
    if not match:
        raise ValueError("Could not extract table name from SQL response")

    result = match.group(1)
    return result.split(".")[-1]  # In case the table name is qualified with a schema


def is_user_sudo(user_role: str) -> bool:
    return user_role.lower() == UserRole.SUDO.value
