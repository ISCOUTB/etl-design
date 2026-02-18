import enum

from sqlalchemy import Enum

# =========== User ===========


class UserRole(enum.Enum):
    SUDO = "sudo"
    USER = "user"


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


user_role_enum = Enum(
    UserRole,
    name="user_role_enum",
    native_enum=True,
    create_type=True,
    schema="public",
)

user_status_enum = Enum(
    UserStatus,
    name="user_status_enum",
    native_enum=True,
    create_type=True,
    schema="public",
)


# =========== Project ===========


class UserProjectType(enum.Enum):
    OWNER = "owner"
    SHARED = "shared"
    VIEWER = "viewer"


user_project_type_enum = Enum(
    UserProjectType,
    name="user_project_type_enum",
    native_enum=True,
    create_type=True,
    schema="public",
)
