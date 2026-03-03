from typing import Optional

from fastapi import APIRouter, status
from proto_utils.database.dtypes import ApiResponse

from src import models, schemas
from src.api.deps import (
    CurrentUser,
    ProjectServiceDep,
    UserProjectServiceDep,
)
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
    projects = project_service.search_projects(
        name=name, user_id=current_user.id, skip=skip, limit=limit
    )
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

    return response


@router.get(
    "/id/{project_id}",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def get_project_by_id(
    project_id: str,
    current_user: CurrentUser,
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

    response = project_service.get_project_by_id(project_id)
    return response


@router.post(
    "/",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_data: schemas.CreateProjectSchema,
    current_user: CurrentUser,
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
    return response


@router.delete(
    "/{project_id}",
    response_model=schemas.ResponseProjectSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
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
    return response


# ============== User Project routes ==============


@router.delete("/{project_id}/flush", status_code=status.HTTP_200_OK)
async def flush_access_project(
    project_id: str,
    current_user: CurrentUser,
    user_project_service: UserProjectServiceDep,
) -> ApiResponse:
    has_permission = PermissionService.has_permission(
        action=Action.flush,
        user=current_user,
        model_key=models.ModelKeys.project,
        model=models.Project(id=project_id),
    )
    if not has_permission:
        raise ForbiddenException()

    user_project_service.flush_access_project(project_id=project_id)
    return ApiResponse(
        status="flushed",
        message=f"Flushed access for project {project_id}",
        data={},
        code=status.HTTP_200_OK,
    )


@router.delete("/{project_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def remove_user_from_project(
    project_id: str,
    user_id: str,
    current_user: CurrentUser,
    user_project_service: UserProjectServiceDep,
) -> ApiResponse:
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
    return ApiResponse(
        status="deleted",
        message=f"Removed user {user_id} from project {project_id}",
        data={},
        code=status.HTTP_200_OK,
    )


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
    user_project_service: UserProjectServiceDep,
) -> schemas.PaginatedResponse[schemas.ResponseUserProjectSchema]:
    has_permission = PermissionService.has_permission(
        action=Action.view, user=current_user, model_key=models.ModelKeys.user_project
    )
    if not has_permission:
        raise ForbiddenException()

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

    user_project = user_project_service.get_user_type_for_project(
        user_id=user_id, project_id=project_id
    )
    return user_project
