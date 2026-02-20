from collections.abc import Callable
from enum import StrEnum
from typing import Dict, Tuple

from src.core.database_sql import SessionLocal
from src.exceptions import IncorrectModel
from src.models import (
    AnyModelKey,
    Model,
    ModelKey,
    ModelKeys,
    UserProjectType,
    UserRole,
    UserStatus,
)
from src.repositories import UserRepository
from src.schemas.token import TokenPayload


def _is_user_active(user: TokenPayload) -> bool:
    with SessionLocal() as db:
        user_record = UserRepository(db=db).get_user_by_id(user.id)

    if user_record is None:
        return False

    return user_record.status == UserStatus.ACTIVE


class Action(StrEnum):
    view = "view"
    search = "search"
    create = "create"
    update = "update"
    delete = "delete"

    # Special action for flushing access to a project, which is different from delete
    flush = "flush"


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
                    up.project_id == model.id and up.user_id == user.id
                    for up in getattr(model, "users", [])
                )
            ),
            Action.search: False,
            Action.create: True,
            Action.update: lambda user, model: (
                model is not None
                and any(
                    up.project_id == model.id
                    and up.user_id == user.id
                    and up.role in (UserProjectType.OWNER, UserProjectType.SHARED)
                    for up in getattr(model, "users", [])  # up: UserProject
                )
            ),
            Action.delete: False,
            Action.flush: lambda user, model: (
                model is not None
                and any(
                    up.project_id == model.id
                    and up.user_id == user.id
                    and up.role == UserProjectType.OWNER
                    for up in getattr(model, "users", [])  # up: UserProject
                )
            ),
        },
        ModelKeys.user_project: {
            Action.view: lambda user, model: (
                model is not None and model.user_id == user.id
            ),
            Action.create: lambda user, model: (
                model is not None
                and model.user_id == user.id
                and model.role == UserProjectType.OWNER
            ),
            Action.update: lambda user, model: (
                model is not None
                and model.user_id == user.id
                and model.role == UserProjectType.OWNER
            ),
            # The only way a user can delete a project record is if the owner of the project
            # deletes all users of the project effectively leaving the project without any users,
            # but still existing in the database. This is a special case that allows users
            # to leave projects they no longer want to be part of, without requiring an admin
            # to delete the project for them.
            Action.delete: lambda user, model: (
                model is not None
                and model.user_id == user.id
                and model.role in (UserProjectType.OWNER)
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
            Action.update: True,
            Action.delete: True,
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
        if model is not None and not isinstance(model, model_key.model_class):  # type: ignore
            raise IncorrectModel(
                f"model type mismatch: expected {model_key.model_class.__name__}, "
                f"got {type(model).__name__}"
            )

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
