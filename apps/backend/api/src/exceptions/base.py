from typing import Any, Dict, Optional


class AppException(Exception):
    status_code: int = 500
    error_code: str = "error:internal-error"
    message: str = "Internal Server Error"

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.status_code = status_code or self.status_code
        self.extra = kwargs

    def _make_response_body(self) -> Dict[str, Any]:
        response = dict(error=self.error_code, message=self.message)
        if self.extra:
            response.update(self.extra)
        return response
