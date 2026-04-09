from datetime import UTC, datetime


def utc_now() -> datetime:
    """
    Get the current UTC time as a datetime object.

    Returns:
        datetime: Current UTC time.
    """
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """
    Get the current UTC time as an ISO 8601 formatted string.

    Returns:
        str: Current UTC time in ISO 8601 format (e.g., "2024-06-01T12:00:00Z").
    """
    return utc_now().isoformat()
