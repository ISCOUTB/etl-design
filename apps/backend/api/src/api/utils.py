from proto_utils.database import DatabaseClient, dtypes


def invalidate_user_cache(
    database_client: DatabaseClient,
    *,
    username: str = "",
    invalidate_lists: bool = False,
) -> None:
    """
    Invalidate user cache based on the username and whether to invalidate lists.

    Args:
        username (str): The username of the user.
        invalidate_lists (bool): Whether to invalidate all user lists.
    """
    patterns_to_delete = []

    if username:
        patterns_to_delete.append(f"{username}:user_info")
        patterns_to_delete.append(f"*:user_info:{username}:*")
        patterns_to_delete.append(f"{username}:user_info:*")

    if invalidate_lists:
        patterns_to_delete.append("all_users:*")

    for pattern in patterns_to_delete:
        try:
            keys = database_client.redis_get_keys(
                dtypes.RedisGetKeysRequest(pattern=pattern), False
            )["keys"]
            database_client.redis_delete(dtypes.RedisDeleteRequest(keys=keys))
        except Exception:
            # TODO: log the error, but don't fail the request if cache invalidation fails
            pass
