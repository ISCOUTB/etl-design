from typing import Optional

from pydantic_core import MultiHostUrl


def create_postgres_uri(
    host: Optional[str],
    port: Optional[int | str],
    user: Optional[str] = None,
    password: Optional[str] = None,
    db_name: Optional[str] = None,
    query: Optional[str] = None,
) -> str:
    """
    Create a PostgreSQL URI from the given parameters.

    Args:
        host (Optional[str]): The host address for the PostgreSQL server.
        port (Optional[int | str]): The port number for the PostgreSQL server.
        user (Optional[str]): The username for authentication.
        password (Optional[str]): The password for authentication.
        db_name (Optional[str]): The name of the database to connect to.
        query (Optional[str]): Additional query parameters for the URI.

    Returns:
        str: A PostgreSQL URI string in the format:
            postgresql://user:password@host:port/db_name?query
    """
    if host is None:
        raise ValueError("Host is required to create a PostgreSQL URI")

    if port is None:
        raise ValueError("Port is required to create a PostgreSQL URI")

    if isinstance(port, str):
        try:
            port = int(port)
        except ValueError:
            raise ValueError(
                f"Port must be an integer or a string representing an integer, got '{port}'"
            )

    return str(
        MultiHostUrl.build(
            scheme="postgresql",
            username=user,
            password=password,
            host=host,
            port=port,
            path=db_name,
            query=query,
        )
    )
