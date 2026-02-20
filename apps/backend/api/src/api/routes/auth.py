from typing import Annotated

from fastapi import APIRouter, Form, status

from src import schemas
from src.api.deps import CurrentUser, SessionDep
from src.services import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_200_OK,
)
async def login(
    form_data: Annotated[schemas.SignInSchema, Form()], db: SessionDep
) -> schemas.ResponseUserSchema:
    response = AuthService(db=db).authenticate_user(
        email=form_data.email, password=form_data.password
    )

    return response


@router.post(
    "sign-up",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(
    form_data: Annotated[schemas.SignUpSchema, Form()], db: SessionDep
) -> schemas.ResponseUserSchema:
    response = AuthService(db=db).register_user(
        email=form_data.email,
        password=form_data.password,
        username=form_data.username,
    )
    return response


@router.get("/test-token")
async def test_token(current_user: CurrentUser) -> schemas.TokenPayload:
    return current_user
