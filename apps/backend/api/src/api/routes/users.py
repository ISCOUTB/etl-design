# TODO: Implement authorization checks
# and check other types of paginations, such as cursor-based pagination
# for better performance on large datasets, is also worth considering in the future.

import json
from typing import Optional

from fastapi import APIRouter, status
from proto_utils.database import dtypes

from src import models, schemas
from src.api.deps import (
    CurrentUser,
    DatabaseClientDep,
    UserProjectServiceDep,
    UserServiceDep,
)
from src.api.utils import invalidate_cache

router = APIRouter()


@router.get(
    "/me", response_model=schemas.ResponseUserSchema, status_code=status.HTTP_200_OK
)
async def get_current_user(
    current_user: CurrentUser,
) -> schemas.ResponseUserSchema:
    return current_user


@router.get(
    "/search",
    response_model=schemas.PaginatedResponse[schemas.ResponseUserSchema],
    status_code=status.HTTP_200_OK,
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


@router.get(
    "/id/{user_id}",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_200_OK,
)
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


@router.get(
    "/search/{email}",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_200_OK,
)
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


@router.get(
    "/{user_id}/projects/{project_id}",
    response_model=schemas.ResponseUserProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_project(
    user_id: str,
    project_id: str,
    current_user: CurrentUser,
    user_project_service: UserProjectServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserProjectSchema:
    cache_key = f"{user_id}:user_info:{project_id}"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.ResponseUserProjectSchema(**json.loads(cached_response["value"]))

    response = user_project_service.get_user_type_for_project(user_id, project_id)

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
        pass

    return response


@router.get(
    "/{user_id}/projects",
    response_model=schemas.PaginatedResponse[schemas.ResponseUserProjectSchema],
    status_code=status.HTTP_200_OK,
)
async def get_projects_for_user(
    user_id: str,
    current_user: CurrentUser,
    user_project_service: UserProjectServiceDep,
    db_client: DatabaseClientDep,
    order_column: Optional[str] = None,
    asc: Optional[bool] = None,
) -> schemas.PaginatedResponse[schemas.ResponseUserProjectSchema]:
    cache_key = f"{user_id}:user_info:projects:page=1"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.PaginatedResponse[schemas.ResponseUserProjectSchema](
            **json.loads(cached_response["value"])
        )

    projects = user_project_service.get_projects_for_user(
        user_id, order_column=order_column, asc=asc
    )
    total = len(projects)
    response = schemas.PaginatedResponse(
        items=projects,
        total=total,
        page=1,
        limit=total,
        total_pages=1,
        has_next=False,
        has_prev=False,
    )

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
        pass

    return response


@router.post(
    "/", response_model=schemas.ResponseUserSchema, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: schemas.CreateUserSchema,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    new_user = user_service.create_user(user_data)
    invalidate_cache(db_client, invalidate_lists=True)
    return new_user


@router.patch(
    "/{user_id}",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: str,
    update_data: schemas.UpdateUserSchema,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    updated_user = user_service.update_user(update_data=update_data, user_id=user_id)
    invalidate_cache(db_client, invalidate_lists=True, name=updated_user.id)
    invalidate_cache(db_client, name=updated_user.email)
    return updated_user


@router.delete(
    "/{user_id}",
    response_model=schemas.ResponseUserSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: str,
    current_user: CurrentUser,
    user_service: UserServiceDep,
    db_client: DatabaseClientDep,
) -> schemas.ResponseUserSchema:
    deleted_user = user_service.delete_user(user_id)
    invalidate_cache(db_client, invalidate_lists=True, name=deleted_user.id)
    invalidate_cache(db_client, name=deleted_user.email)
    return deleted_user
