import json
from typing import Optional

from fastapi import APIRouter, status
from proto_utils.database import dtypes

from src import models, schemas
from src.api.deps import (
    CurrentUser,
    DatabaseClientDep,
    ProjectServiceDep,
    UserProjectServiceDep,
)
from src.api.utils import invalidate_cache
from src.exceptions import ForbiddenException
from src.services.permissions import Action, PermissionService

router = APIRouter()

# ============== Project routes ==============


@router.get(
    "/search",
    response_model=schemas.PaginatedResponse[schemas.ResponseProjectSchema],
    status_code=status.HTTP_200_OK,
)
async def search_projects(
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    name: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> schemas.PaginatedResponse[schemas.ResponseProjectSchema]:
    has_permission = PermissionService.has_permission(
        action=Action.search, user=current_user, model_key=models.ModelKeys.project
    )
    if not has_permission:
        raise ForbiddenException()

    page = (skip // limit) + 1
    cache_key = f"all_projects:name={name}:limit={limit}:page={page}"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.PaginatedResponse(**json.loads(cached_response["value"]))

    projects = project_service.search_projects(name=name, skip=skip, limit=limit)
    total = project_service.count_projects(name=name)
    response = schemas.PaginatedResponse(
        items=projects,
        total=total,
        page=page,
        limit=limit,
        total_pages=(total // limit) + (1 if total % limit > 0 else 0),
        has_next=(skip + limit) < total,
        has_prev=skip > 0,
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
        # TODO: log the error, but don't fail the request if cache set fails
        pass

    return response


@router.get(
    "/id/{project_id}",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def get_project_by_id(
    project_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
) -> schemas.ResponseProjectSchema:
    has_permission = PermissionService.has_permission(
        action=Action.view,
        user=current_user,
        model_key=models.ModelKeys.project,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    cache_key = f"{project_id}:project_info"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.ResponseProjectSchema(**json.loads(cached_response["value"]))

    response = project_service.get_project_by_id(project_id)

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
    "/",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_data: schemas.CreateProjectSchema,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
    user_project_service: UserProjectServiceDep,
) -> schemas.ResponseProjectSchema:
    has_permission = PermissionService.has_permission(
        action=Action.create, user=current_user, model_key=models.ModelKeys.project
    )
    if not has_permission:
        raise ForbiddenException()

    response = project_service.create_project(project_data)

    # If a regular user creates a project, automatically add them as the owner of the project
    if current_user.role == models.UserRole.USER:
        user_project_service.add_user_to_project(
            schemas.CreateUserProjectSchema(
                user_id=current_user.id,
                project_id=response.id,
                role=models.UserProjectType.OWNER,
            )
        )

    invalidate_cache(db_client, invalidate_lists=True, scope="project")
    return response


@router.patch(
    "/{project_id}",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def update_project(
    project_id: str,
    project_data: schemas.UpdateProjectSchema,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
) -> schemas.ResponseProjectSchema:
    has_permission = PermissionService.has_permission(
        action=Action.update,
        user=current_user,
        model_key=models.ModelKeys.project,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    response = project_service.update_project(
        project_data=project_data, project_id=project_id
    )
    invalidate_cache(db_client, name=project_id, invalidate_lists=True, scope="project")
    return response


@router.delete(
    "/{project_id}",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    project_service: ProjectServiceDep,
) -> schemas.ResponseProjectSchema:
    has_permission = PermissionService.has_permission(
        action=Action.delete,
        user=current_user,
        model_key=models.ModelKeys.project,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    response = project_service.delete_project(project_id=project_id)
    invalidate_cache(db_client, name=project_id, invalidate_lists=True, scope="project")
    return response


# ============== User Project routes ==============


@router.delete("/{project_id}/flush", status_code=status.HTTP_204_NO_CONTENT)
async def flush_access_project(
    project_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    user_project_service: UserProjectServiceDep,
) -> None:
    has_permission = PermissionService.has_permission(
        action=Action.flush,
        user=current_user,
        model_key=models.ModelKeys.project,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    user_project_service.flush_access_project(project_id=project_id)
    invalidate_cache(
        db_client, name=project_id, invalidate_lists=True, scope="user_project"
    )
    return None


@router.delete("/{project_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_project(
    project_id: str,
    user_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    user_project_service: UserProjectServiceDep,
) -> None:
    has_permission = PermissionService.has_permission(
        action=Action.delete,
        user=current_user,
        model_key=models.ModelKeys.user_project,
        model=models.UserProject(user_id=user_id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    user_project_service.remove_user_from_project(
        project_id=project_id, user_id=user_id
    )
    invalidate_cache(
        db_client, name=project_id, invalidate_lists=True, scope="user_project"
    )
    invalidate_cache(
        db_client, name=user_id, invalidate_lists=True, scope="user_project"
    )
    return None


# A priori, a project shouldn't have so many users, so we won't implement pagination here.
# If we need to, we can add it later and update the cache key accordingly.
@router.get(
    "/{project_id}/users",
    response_model=schemas.PaginatedResponse[schemas.ResponseUserProjectSchema],
    status_code=status.HTTP_200_OK,
)
async def get_users_for_project(
    project_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    user_project_service: UserProjectServiceDep,
) -> schemas.PaginatedResponse[schemas.ResponseUserProjectSchema]:
    has_permission = PermissionService.has_permission(
        action=Action.view, user=current_user, model_key=models.ModelKeys.user_project
    )
    if not has_permission:
        raise ForbiddenException()

    cache_key = f"{project_id}:user_project_info"
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

    users = user_project_service.get_users_for_project(project_id=project_id)
    response = schemas.PaginatedResponse(
        items=users,
        total=len(users),
        page=1,
        limit=len(users),
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


@router.get(
    "/{project_id}/users/{user_id}",
    response_model=schemas.ResponseUserProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_project(
    project_id: str,
    user_id: str,
    current_user: CurrentUser,
    db_client: DatabaseClientDep,
    user_project_service: UserProjectServiceDep,
) -> schemas.ResponseUserProjectSchema:
    has_permission = PermissionService.has_permission(
        action=Action.view,
        user=current_user,
        model_key=models.ModelKeys.user_project,
        model=models.UserProject(user_id=user_id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    cache_key = f"{user_id}:user_project_info:{project_id}"
    try:
        cached_response = db_client.redis_get(
            dtypes.RedisGetRequest(key=cache_key), False
        )
    except Exception:
        cached_response = dtypes.RedisGetResponse(found=False, value=None)

    if cached_response["found"] and cached_response["value"] is not None:
        return schemas.ResponseUserProjectSchema(**json.loads(cached_response["value"]))

    user_project = user_project_service.get_user_type_for_project(
        user_id=user_id, project_id=project_id
    )
    try:
        db_client.redis_set(
            dtypes.RedisSetRequest(
                key=cache_key,
                value=json.dumps(user_project.model_dump(mode="json")),
                expiration=None,
            ),
            False,
        )
    except Exception:
        pass

    return user_project
