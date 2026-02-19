from fastapi import APIRouter

from src import schemas
from src.api.deps import CurrentUser

router = APIRouter()


@router.get("/test-token")
async def test_token(current_user: CurrentUser) -> schemas.ResponseUserSchema:
    return current_user
