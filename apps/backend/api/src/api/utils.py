from typing import Literal

from proto_utils.database import DatabaseClient, dtypes

CacheScope = Literal["user", "project", "user_project"]


def invalidate_cache(
    database_client: DatabaseClient,
    *,
    name: str = "",
    invalidate_lists: bool = False,
    scope: CacheScope = "user",
) -> None:
    """
    Invalidate user cache based on the name and whether to invalidate lists.

    Args:
        name (str): The name of the object.
        invalidate_lists (bool): Whether to invalidate all user lists.
        scope (CacheScope): The scope of the cache to invalidate ("user", "project", or "user_project").
    """
    patterns_to_delete = []

    if name:
        patterns_to_delete.append(f"{name}:{scope}_info")
        patterns_to_delete.append(f"*:{scope}_info:{name}:*")
        patterns_to_delete.append(f"{name}:{scope}_info:*")

    if invalidate_lists:
        patterns_to_delete.append(f"all_{scope}s:*")

    for pattern in patterns_to_delete:
        try:
            keys = database_client.redis_get_keys(
                dtypes.RedisGetKeysRequest(pattern=pattern), False
            )["keys"]
            database_client.redis_delete(dtypes.RedisDeleteRequest(keys=keys))
        except Exception:
            # TODO: log the error, but don't fail the request if cache invalidation fails
            pass
