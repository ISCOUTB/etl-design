import uuid

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from uuidv7 import uuid7

from src.core.database_sql import BaseModel
from src.models.dtypes import user_project_type_enum
from src.utils import utc_now


class Project(BaseModel):
    __tablename__ = "project"
    __table_args__ = (
        Index("idx_project_name", "name"),
        UniqueConstraint("name", name="uq_project_name"),
        {"schema": "public"},
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.UUID(str(uuid7())),
        nullable=False,
    )
    name = Column(String, default=None, nullable=False)
    description = Column(String, default=None, nullable=True)

    # Database connection info
    provider = Column(String, default=None, nullable=True)
    db_host = Column(String, default=None, nullable=True)
    db_port = Column(String, default=None, nullable=True)
    db_user = Column(String, default=None, nullable=True)
    db_password = Column(String, default=None, nullable=True)
    db_name = Column(String, default=None, nullable=True)
    db_netloc = Column(String, default=None, nullable=True)
    db_params = Column(String, default=None, nullable=True)

    # Datetimes
    created_at = Column(
        DateTime(timezone=True),
        default=None,
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=None,
        nullable=False,
        server_default=text("NOW()"),
        onupdate=utc_now,
    )

    # Relationships
    users = relationship("UserProject", back_populates="project", uselist=True)


class UserProject(BaseModel):
    __tablename__ = "user_project"
    __table_args__ = (
        Index("idx_user_project_project_id", "project_id"),
        Index("idx_user_project_role", "role"),
        {"schema": "public"},
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.user.id"),
        primary_key=True,
        nullable=False,
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.project.id"),
        primary_key=True,
        nullable=False,
    )
    role = Column(user_project_type_enum, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=None,
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=None,
        nullable=False,
        server_default=text("NOW()"),
        onupdate=utc_now,
    )

    user = relationship("User", back_populates="projects")
    project = relationship("Project", back_populates="users")
