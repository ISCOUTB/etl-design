from typing import Annotated

from fastapi import APIRouter, Form

from src import schemas
from src.api.deps import CurrentUser, SessionDep
from src.services import AuthService

router = APIRouter()


@router.post("/")
async def login(
    form_data: Annotated[schemas.SignInSchema, Form()], db: SessionDep
) -> schemas.ResponseUserSchema:
    response = AuthService(db=db).authenticate_user(
        email=form_data.email, password=form_data.password
    )

    return response


@router.get("/test-token")
async def test_token(current_user: CurrentUser) -> schemas.ResponseUserSchema:
    return current_user
