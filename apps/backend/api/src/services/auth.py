import base64
import json

from jwcrypto import jwe, jwk
from sqlalchemy.orm import Session

from src import models, schemas
from src.core.config import settings
from src.core.security import derive_key, verify_password
from src.exceptions import (
    EmailInUseException,
    InvalidCredentialsException,
    TokenExpiredException,
    UnauthenticatedException,
)
from src.repositories import UserRepository
from src.services.parser import ParserService
from src.utils import utc_now


class AuthService:
    def __init__(self, *, db: Session):
        self.user_repository = UserRepository(db=db)

    def authenticate_user(self, email: str, password: str):
        user = self.user_repository.get_by_email(email, True)
        if not user or not verify_password(password, str(user.password)):
            raise InvalidCredentialsException()

        return ParserService.parse_user(user)

    def register_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> schemas.ResponseUserSchema:
        existing_user = self.user_repository.get_by_email(email)
        if existing_user:
            raise EmailInUseException()

        try:
            user = self.user_repository.create_user(
                schemas.CreateUserSchema(
                    name=username,
                    email=email,
                    password=password,
                    role=models.UserRole.USER,
                )
            )
            self.user_repository.db.commit()
        except Exception as e:
            self.user_repository.db.rollback()
            raise e

        return ParserService.parse_user(user)

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

    # This is actually a helper function, it's not essential to all the backend service,
    # because all the sessions are managed directly in the frontend, and here, in the backend,
    # we just decode the token and get the user information, but we don't manage the session itself.
    @staticmethod
    def encode_access_token(payload: schemas.TokenPayload) -> str:
        key = jwk.JWK(
            kty="oct",
            k=base64.urlsafe_b64encode(
                derive_key(secret=settings.SECRET_KEY, info=settings.AUTH_INFO)
            )
            .decode()
            .rstrip("="),
        )

        j = jwe.JWE(
            plaintext=json.dumps(payload.model_dump()).encode("utf-8"),
            protected='{"alg": "dir", "enc": "A256GCM"}',
        )
        j.add_recipient(key)
        return j.serialize()
