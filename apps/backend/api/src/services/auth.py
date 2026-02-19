import base64
import json

from jwcrypto import jwe, jwk
from sqlalchemy.orm import Session

from src import schemas
from src.core.config import settings
from src.core.security import derive_key, verify_password
from src.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    UnauthenticatedException,
)
from src.repositories import UserRepository
from src.utils import utc_now


class AuthService:
    def __init__(self, *, db: Session):
        self.user_repository = UserRepository(db=db)

    def authenticate_user(self, email: str, password: str):
        user = self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        return user

    def get_current_user(self, token: str):
        try:
            payload_token = self.decode_access_token(token)
        except Exception as e:
            raise UnauthenticatedException() from e

        if payload_token.exp < utc_now().timestamp():
            raise TokenExpiredException()

    @staticmethod
    def decode_access_token(token: str) -> schemas.TokenPayload:
        try:
            key = jwk.JWK(
                kty="oct",
                k=base64.urlsafe_b64encode(
                    derive_key(secret=settings.SECRET_KEY, info=settings.AUTH_INFO)
                )
                .decode()
                .rstrip("="),
            )

            j = jwe.JWE()
            j.deserialize(token)
            j.decrypt(key)

            payload = json.loads(j.payload.decode("utf-8"))
            payload_token = schemas.TokenPayload(**payload)

            if payload_token.exp < utc_now().timestamp():
                raise TokenExpiredException()
        except (TokenExpiredException, UnauthenticatedException):
            raise
        except Exception as e:
            raise UnauthenticatedException() from e
        
        return payload_token
