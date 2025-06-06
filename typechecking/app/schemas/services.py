from typing import TypedDict, Optional


class FileInfo(TypedDict):
    """
    TypedDict for file information.
    Contains the file name, size, and type.
    """
    filename: Optional[str]
    size: Optional[int]
    content_type: Optional[str]
    is_supported: bool
