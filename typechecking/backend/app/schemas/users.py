from pydantic import BaseModel
from typing import Literal, Optional, TypedDict

Roles = Literal["admin", "user"]
Sex = Literal[
    "M",  # Male
    "F",  # Female
    "O",  # Other
    "N",  # Not specified
    "U",  # Unknown
    "X",  # Prefer not to say
]


class RolesInfo(TypedDict):
    rol: Roles
    is_active: bool


class BaseUser(BaseModel):
    username: str
    name: Optional[str] = None
    surname: Optional[str] = None
    sex: Optional[Sex] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class User(BaseUser):
    rol: Roles


class LoginUser(BaseModel):
    username: str
    password: str
    rol: Roles


class SearchUser(BaseModel):
    username: str
    rol: Roles


class CreateUser(User):
    password: str


class UpdateUser(BaseUser):
    password: Optional[str] = None
    rol: Optional[Roles] = None


class AllUser(BaseUser):
    roles: list[RolesInfo]
