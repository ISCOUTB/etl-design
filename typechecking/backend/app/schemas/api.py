from pydantic import BaseModel
from typing import TypedDict, TypeVar, Generic

# TypeVar for generic pagination
T = TypeVar("T")


class ApiResponse(BaseModel):
    """
    Base model for API responses.

    Attributes:
        status (str): The status of the response, e.g., "success" or "error".
        code (int): The HTTP status code associated with the response.
        message (str): A message providing additional information about the response.
        data (dict, optional): The data returned in the response, if any. Defaults to None.
    """

    status: str
    code: int
    message: str
    data: dict = None


class Paginated(TypedDict, Generic[T]):
    """
    Base model for paginated responses.

    Attributes:
        total (int): The total number of items available.
        page (int): The current page number.
        limit (int): The number of items per page.
        total_pages (int): The total number of pages available.
        has_next (bool): Indicates if there is a next page.
        has_prev (bool): Indicates if there is a previous page.
        items (list[T]): The list of items on the current page.
    """

    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    items: list[T]
