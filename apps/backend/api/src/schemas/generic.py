from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase


class _Base(DeclarativeBase):
    """Base class for all sqlalchemy models"""

    pass


T = TypeVar("T", bound=_Base)


class DeleteResult(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    status: Literal["deleted", "not_found", "has_dependencies"]
    obj: Optional[T] = None
