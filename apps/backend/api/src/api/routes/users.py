# TODO: check other types of paginations, such as cursor-based pagination
# for better performance on large datasets, is also worth considering in the future.

from typing import Optional

from fastapi import APIRouter, status

from src import models, schemas
from src.api.deps import (
    CurrentUser,
    DatabaseClientDep,
    UserProjectServiceDep,
    UserServiceDep,
)
from src.exceptions import ForbiddenException
from src.services.permissions import Action, PermissionService

router = APIRouter()

# ============== User routes ==============


@router.get(
    "/me", response_model=schemas.ResponseUserSchema, status_code=status.HTTP_200_OK
)
async def get_current_user(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> schemas.ResponseUserSchema:
    response = user_service.get_user_by_id(current_user.sub)
    return response


@router.get(
    "/search",
    response_model=schemas.PaginatedResponse[schemas.ResponseUserSchema],
    status_code=status.HTTP_200_OK,
)
async def search_users(
    current_user: CurrentUser,
    user_service: UserServiceDep,
    name: Optional[str] = None,
    email: Optional[str] = None,
    active: bool = True,
    role: Optional[models.UserRole] = None,
    skip: int = 0,
    limit: int = 10,
) -> schemas.PaginatedResponse[schemas.ResponseUserSchema]:
    has_permission = PermissionService.has_permission(
        action=Action.search, user=current_user, model_key=models.ModelKeys.user
    )
    if not has_permission:
        raise ForbiddenException()

    page = (skip // limit) + 1
    users = user_service.search_users(
        active_only=active,
        role=role,
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
) -> schemas.ResponseUserSchema:
    has_permission = PermissionService.has_permission(
        action=Action.view,
        user=current_user,
        model_key=models.ModelKeys.user,
        model=models.User(id=user_id),
    )
    if not has_permission:
        raise ForbiddenException()

    response = user_service.get_user_by_id(user_id)
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
) -> schemas.ResponseUserSchema:
    has_permission = PermissionService.has_permission(
        action=Action.search, user=current_user, model_key=models.ModelKeys.user
    )
    if not has_permission:
        raise ForbiddenException()

    response = user_service.get_user_by_email(email)
    return response


@router.post(
    "/", response_model=schemas.ResponseUserSchema, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: schemas.CreateUserSchema,
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> schemas.ResponseUserSchema:
    has_permission = PermissionService.has_permission(
        action=Action.create, user=current_user, model_key=models.ModelKeys.user
    )
    if not has_permission:
        raise ForbiddenException()

    new_user = user_service.create_user(user_data)
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
) -> schemas.ResponseUserSchema:
    has_permission = PermissionService.has_permission(
        action=Action.update,
        user=current_user,
        model_key=models.ModelKeys.user,
        model=models.User(id=user_id),
    )
    if not has_permission:
        raise ForbiddenException()

    updated_user = user_service.update_user(update_data=update_data, user_id=user_id)
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
) -> schemas.ResponseUserSchema:
    has_permission = PermissionService.has_permission(
        action=Action.delete,
        user=current_user,
        model_key=models.ModelKeys.user,
        model=models.User(id=user_id),
    )
    if not has_permission:
        raise ForbiddenException()

    deleted_user = user_service.delete_user(user_id)
    return deleted_user


# ============== UserProject routes ==============


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
    has_permission = PermissionService.has_permission(
        action=Action.view,
        user=current_user,
        model_key=models.ModelKeys.user_project,
        model=models.UserProject(user_id=user_id, project_id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    response = user_project_service.get_user_type_for_project(user_id, project_id)
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
    order_column: Optional[str] = None,
    asc: Optional[bool] = None,
) -> schemas.PaginatedResponse[schemas.ResponseUserProjectSchema]:
    has_permission = PermissionService.has_permission(
        action=Action.view,
        user=current_user,
        model_key=models.ModelKeys.user_project,
        model=models.UserProject(user_id=user_id),
    )
    if not has_permission:
        raise ForbiddenException()

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

    return response
