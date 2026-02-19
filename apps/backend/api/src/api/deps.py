from collections.abc import Generator
from typing import Annotated, Optional

from fastapi import Depends, Header
from messaging_utils.core.connection_params import messaging_params
from messaging_utils.messaging.publishers import Publisher
from proto_utils.database.base_client import DatabaseClient
from sqlalchemy.orm import Session

from src import schemas
from src.core.config import settings
from src.core.database_sql import SessionLocal
from src.exceptions import UnauthenticatedException
from src.services import AuthService, ProjectService, UserProjectService, UserService


def get_db_client() -> Generator[DatabaseClient, None, None]:
    db_client = DatabaseClient(
        settings.DATABASE_CONNECTION_CHANNEL,
        max_retries=settings.DATABASE_MAX_RETRIES,
        retry_delay=settings.DATABASE_RETRY_DELAY_SECONDS,
        backoff=settings.DATABASE_BACKOFF_MULTIPLIER,
    )
    try:
        yield db_client
    finally:
        db_client.close()


def get_sql_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_publisher() -> Generator[Publisher, None, None]:
    params = messaging_params.copy()
    exchange_info = params.pop("exchange")

    publisher = Publisher(
        params=params,
        exchange_info=exchange_info,  # type: ignore
        max_tries=settings.RABBITMQ_MAX_RETRIES,
        retry_delay=settings.RABBITMQ_RETRY_DELAY_SECONDS,
        backoff=settings.RABBITMQ_BACKOFF_MULTIPLIER,
    )

    try:
        yield publisher
    finally:
        publisher.close()


SessionDep = Annotated[Session, Depends(get_sql_db)]
DatabaseClientDep = Annotated[DatabaseClient, Depends(get_db_client)]
PublisherDep = Annotated[Publisher, Depends(get_publisher)]

# Services dependencies


def get_user_service(db: SessionDep) -> UserService:
    return UserService(db=db)


def get_auth_service(db: SessionDep) -> AuthService:
    return AuthService(db=db)


def get_project_service(db: SessionDep) -> ProjectService:
    return ProjectService(db=db)


def get_user_project_service(db: SessionDep) -> UserProjectService:
    return UserProjectService(db=db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
UserProjectServiceDep = Annotated[UserProjectService, Depends(get_user_project_service)]


# Decode token and get current user dependency
def get_current_user(
    user_service: UserServiceDep,
    authorization: Optional[str | None] = Header(default=None, alias="Authorization"),
) -> schemas.ResponseUserSchema:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthenticatedException()

    token = authorization.removeprefix("Bearer ").strip()
    payload_token = AuthService.decode_access_token(token)

    try:
        user = user_service.get_user_by_id(payload_token.sub)
    except Exception as e:
        raise UnauthenticatedException() from e

    return user


CurrentUser = Annotated[schemas.ResponseUserSchema, Depends(get_current_user)]
