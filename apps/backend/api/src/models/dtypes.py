import enum

from sqlalchemy import Enum

# =========== User ===========


class UserRole(enum.Enum):
    SUDO = "sudo"
    USER = "user"


class Status(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


user_role_enum = Enum(
    UserRole,
    name="user_role_enum",
    native_enum=True,
    create_type=True,
    schema="public",
)

status_enum = Enum(
    Status,
    name="status_enum",
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


# ========== Uploads ===========


class TaskStatus(enum.Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


task_status_enum = Enum(
    TaskStatus,
    name="task_status_enum",
    native_enum=True,
    create_type=True,
    schema="public",
)
