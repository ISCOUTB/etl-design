from collections.abc import Callable
from enum import StrEnum
from typing import Dict, List, Tuple

from src.core.database_sql import SessionLocal
from src.models import (
    AnyModelKey,
    Model,
    ModelKey,
    ModelKeys,
    Status,
    UserProject,
    UserProjectType,
    UserRole,
)
from src.repositories import UserProjectRepository, UserRepository
from src.schemas.token import TokenPayload


def _is_user_active(user: TokenPayload) -> bool:
    with SessionLocal() as db:
        user_record = UserRepository(db=db).get_user_by_id(user.id)

    if user_record is None:
        return False

    return user_record.status == Status.ACTIVE  # type: ignore


def _load_user_projects_for_project(project_id: str) -> List[UserProject]:
    with SessionLocal() as db:
        user_projects = UserProjectRepository(db=db).get_users_for_project(
            project_id=project_id
        )

    return user_projects if user_projects else []


def _load_user_project_model(user_id: str, project_id: str) -> UserProject | None:
    with SessionLocal() as db:
        user_project = UserProjectRepository(db=db).get_user_type_for_project(
            user_id, project_id
        )

    if user_project is None:
        return None

    return user_project


class Action(StrEnum):
    view = "view"
    search = "search"
    create = "create"
    update = "update"
    delete = "delete"

    # Special action for flushing access to a project, which is different from delete
    flush = "flush"

    # Special actions for user_project model. This action is used by a owner of a project
    # to add a new member to a project. The logic behind this action is different from the
    # normal create action
    invite = "invite"

    # Special operations for uploads
    validate = "validate"
    process = "process"
    insert = "insert"
    table = "table"


CheckPermission = bool | Callable[[TokenPayload, Model | None], bool]


ROLE_HIERARCHY: Dict[UserRole, Tuple[UserRole, ...]] = {
    UserRole.SUDO: (UserRole.SUDO, UserRole.USER),
    UserRole.USER: (UserRole.USER,),
}


# Maybe there are some misinterpretations in the permissions (and errors with lambda functions),
# but this is a good starting point that can be easily modified as we go along and discover
# edge cases that we didn't think of initially. The idea is to have a flexible
# and extensible permission system that can accommodate different types of
# permissions and roles as needed.
ROLES: Dict[UserRole, Dict[AnyModelKey, Dict[Action, CheckPermission]]] = {
    # User can only view and update their own user record, and view/update projects they are part of
    # and the projects they create, they are the owner, and they can share them with other users,
    # but they cannot delete any project or user record
    UserRole.USER: {
        ModelKeys.user: {
            Action.view: lambda user, model: (
                model is not None
                and (
                    (model.id == user.id if hasattr(model, "id") else False)
                    or (
                        model.user_id == user.id if hasattr(model, "user_id") else False
                    )
                )
                and _is_user_active(user)
            ),
            Action.search: False,
            Action.create: False,
            Action.update: lambda user, model: (
                model is not None and model.id == user.id and _is_user_active(user)
            ),
            Action.delete: lambda user, model: (
                model is not None and model.id == user.id and _is_user_active(user)
            ),
        },
        ModelKeys.project: {
            Action.view: lambda user, model: (
                model is not None
                and any(
                    str(up.project_id) == model.id and str(up.user_id) == user.id
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.search: True,
            Action.create: True,
            Action.update: lambda user, model: (
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.delete: False,
            Action.flush: lambda user, model: (
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
        },
        ModelKeys.user_project: {
            Action.view: lambda user, model: (
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and str(repo_model.user_id) == user.id
            ),
            Action.create: False,
            Action.invite: lambda user, model: (
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and str(repo_model.user_id) == user.id
                and repo_model.role in {UserProjectType.OWNER}
            ),
            Action.update: lambda user, model: (
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and str(repo_model.user_id) == user.id
                and repo_model.role in {UserProjectType.OWNER}
            ),
            # The only way a user can delete a project record is if the owner of the project
            # deletes all users of the project effectively leaving the project without any users,
            # but still existing in the database. This is a special case that allows users
            # to leave projects they no longer want to be part of, without requiring an admin
            # to delete the project for them.
            Action.delete: lambda user, model: (
                model is not None
                and model.user_id == user.id
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and repo_model.role in {UserProjectType.OWNER}
            ),
        },
        ModelKeys.cache: {
            Action.view: False,
            Action.search: False,
            Action.create: False,
            Action.update: False,
            Action.delete: False,
            Action.flush: False,
        },
        ModelKeys.schemas: {
            Action.view: lambda user, model: (  # model: UserProject
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and user.id == str(repo_model.user_id)
            ),
            Action.search: False,
            Action.create: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.update: lambda user, model: (  # model: UserProject
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and user.id == str(repo_model.user_id)
                and repo_model.role in {UserProjectType.OWNER, UserProjectType.SHARED}
            ),
            Action.delete: lambda user, model: (  # model: UserProject
                model is not None
                and (
                    (
                        repo_model := _load_user_project_model(
                            str(model.user_id), str(model.project_id)
                        )
                    )
                    is not None
                )
                and user.id == str(repo_model.user_id)
                and repo_model.role in {UserProjectType.OWNER}
            ),
        },
        ModelKeys.task: {
            Action.view: False,
            Action.search: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id and str(up.user_id) == user.id
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
        },
        ModelKeys.upload: {
            Action.validate: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.process: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.insert: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
            Action.table: lambda user, model: (  # model: Project
                model is not None
                and any(
                    str(up.project_id) == model.id
                    and str(up.user_id) == user.id
                    and up.role in {UserProjectType.OWNER, UserProjectType.SHARED}
                    for up in _load_user_projects_for_project(model.id)
                )
            ),
        },
    },
    UserRole.SUDO: {
        ModelKeys.user: {
            Action.view: True,
            Action.search: True,
            Action.create: True,
            Action.update: True,
            Action.delete: True,
        },
        ModelKeys.project: {
            Action.view: True,
            Action.search: True,
            Action.create: True,
            Action.update: True,
            Action.delete: True,
            Action.flush: True,
        },
        ModelKeys.user_project: {
            Action.view: True,
            Action.search: True,
            Action.create: True,
            Action.invite: True,
            Action.update: True,
            Action.delete: True,
        },
        ModelKeys.cache: {
            Action.view: True,
            Action.search: True,
            Action.create: True,
            Action.update: True,
            Action.delete: True,
            Action.flush: True,
        },
        ModelKeys.schemas: {
            Action.view: True,
            Action.search: True,
            Action.create: True,
            Action.update: True,
            Action.delete: True,
        },
        ModelKeys.task: {
            Action.view: True,
            Action.search: True,
        },
        ModelKeys.upload: {
            Action.validate: True,
            Action.process: True,
            Action.insert: True,
            Action.table: True,
        },
    },
}


class PermissionService(object):
    @classmethod
    def has_permission(
        cls,
        *,
        action: Action,
        user: TokenPayload,
        model_key: ModelKey[Model],
        model: Model | None = None,
    ) -> bool:
        for role in ROLE_HIERARCHY.get(user.role, (user.role,)):
            model_permissions = ROLES.get(role, {}).get(model_key, {})
            permission = model_permissions.get(action, False)

            if permission is None:
                continue

            if permission is True:
                return True

            if permission is False:
                continue

            if callable(permission) and permission(user, model):
                return True

        return False
