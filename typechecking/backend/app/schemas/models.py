from typing import Optional
from pydantic import BaseModel
from app.schemas.users import Sex, Roles


class UserInfo(BaseModel):
    username: str
    name: Optional[str] = None
    surname: Optional[str] = None
    sex: Optional[Sex] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class UserRoles(BaseModel):
    username: str
    rol: Roles  # type: ignore
    password: str
    is_active: bool = True
    inactivity: str | None = None

    class Config:
        from_attributes = True
