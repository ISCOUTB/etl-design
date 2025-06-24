from pydantic import BaseModel
from app.schemas.users import Roles


class TokenPayload(BaseModel):
    username: str
    rol: Roles


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
