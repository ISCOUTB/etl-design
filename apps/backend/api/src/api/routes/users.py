# TODO: Implement authorization checks
# and check other types of paginations, such as cursor-based pagination
# for better performance on large datasets, is also worth considering in the future.

import json
from typing import Optional

from fastapi import APIRouter
from proto_utils.database import dtypes

from src import models, schemas
from src.api.deps import CurrentUser, DatabaseClientDep, UserServiceDep
from src.api.utils import invalidate_user_cache

router = APIRouter()


@router.get("/me", response_model=schemas.ResponseUserSchema)
async def get_current_user(
    current_user: CurrentUser,
) -> schemas.ResponseUserSchema:
    return current_user


@router.get(
    "/search", response_model=schemas.PaginatedResponse[schemas.ResponseUserSchema]
)
async def search_users(
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    user_service: UserServiceDep,
    name: Optional[str] = None,
    email: Optional[str] = None,
    active: bool = True,
    role: Optional[models.UserRole] = None,
    skip: int = 0,
    limit: int = 10,
) -> schemas.PaginatedResponse[schemas.ResponseUserSchema]:
    page = (skip // limit) + 1
    role_str = role.value if role else "any"
    cache_key = f"all_users:active={active}:rol={role_str}:limit={limit}:page={page}"
    cached_response = db_client.redis_get(dtypes.RedisGetRequest(key=cache_key))
    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.PaginatedResponse(**json.loads(cached_response["value"]))

    users = user_service.search_users(
        active_only=True,
        name=name,
        email=email,
        skip=skip,
        limit=limit,
    )
    total = user_service.count_users(
        active_only=True,
        name=name,
        email=email,
    )
    response = schemas.PaginatedResponse(
        items=users,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total // limit) + (1 if total % limit > 0 else 0),
        has_next=(skip + limit) < total,
        has_prev=skip > 0,
    )

    db_client.redis_set(
        dtypes.RedisSetRequest(
            key=cache_key,
            value=json.dumps(response.model_dump(mode="json")),
            expiration=None,
        )
    )
    return response


@router.get("/id/{user_id}", response_model=schemas.ResponseUserSchema)
async def get_user_by_id(
    user_id: str,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    cache_key = f"{user_id}:user_info"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.ResponseUserSchema(**json.loads(cached_response["value"]))

    response = user_service.get_user_by_id(user_id)

    try:
        db_client.redis_set(
            dtypes.RedisSetRequest(
                key=cache_key,
                value=json.dumps(response.model_dump(mode="json")),
                expiration=None,
            ),
            False,
        )
    except Exception:
        # TODO: log the error, but don't fail the request if caching fails
        pass

    return response


@router.get("/search/{email}", response_model=schemas.ResponseUserSchema)
async def get_user_by_email(
    email: str,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    cache_key = f"{email}:user_info"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.ResponseUserSchema(**json.loads(cached_response["value"]))

    response = user_service.get_user_by_email(email)

    try:
        db_client.redis_set(
            dtypes.RedisSetRequest(
                key=cache_key,
                value=json.dumps(response.model_dump(mode="json")),
                expiration=None,
            )
        )
    except Exception:
        # TODO: log the error, but don't fail the request if caching fails
        pass

    return response


@router.post("/", response_model=schemas.ResponseUserSchema)
async def create_user(
    user_data: schemas.CreateUserSchema,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    new_user = user_service.create_user(user_data)
    invalidate_user_cache(db_client, invalidate_lists=True)
    return new_user


@router.patch("/{user_id}", response_model=schemas.ResponseUserSchema)
async def update_user(
    user_id: str,
    update_data: schemas.UpdateUserSchema,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    updated_user = user_service.update_user(update_data=update_data, user_id=user_id)
    invalidate_user_cache(db_client, invalidate_lists=True, username=updated_user.id)
    invalidate_user_cache(db_client, username=updated_user.email)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    deleted_user = user_service.delete_user(user_id)
    invalidate_user_cache(db_client, invalidate_lists=True, username=deleted_user.id)
    invalidate_user_cache(db_client, username=deleted_user.email)
    return deleted_user
