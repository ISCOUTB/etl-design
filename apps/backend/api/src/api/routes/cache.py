import json

from fastapi import APIRouter
from proto_utils.database import dtypes

from src.api.deps import CurrentUser, DatabaseClientDep
from src.exceptions import ForbiddenException
from src.services.permissions import Action, ModelKeys, PermissionService

router = APIRouter()


@router.get("/")
async def get_cache(db_client: DatabaseClientDep, current_user: CurrentUser) -> dict:
    """
    Get all cached data from Redis.
    This endpoint retrieves all keys and their values from the Redis cache.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.search,
        model_key=ModelKeys.cache,
    )
    if not has_permission:
        raise ForbiddenException()

    response = await db_client.redis_get_cache_async()
    return dict(map(lambda x: (x[0], json.loads(x[1])), response["cache"].items()))


@router.delete("/clear")
async def clear_cache(
    db_client: DatabaseClientDep, current_user: CurrentUser
) -> dtypes.RedisClearCacheResponse:
    """
    Clear the Redis cache.
    This endpoint clears all cached data in Redis.
    """
    has_permission = PermissionService.has_permission(
        user=current_user,
        action=Action.flush,
        model_key=ModelKeys.cache,
    )
    if not has_permission:
        raise ForbiddenException()

    return await db_client.clear_cache_async()
