from pydantic import BaseModel


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
