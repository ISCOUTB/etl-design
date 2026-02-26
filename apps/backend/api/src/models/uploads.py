from datetime import timedelta

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.core.database_sql import BaseModel
from src.models.dtypes import TaskStatus, task_status_enum
from src.utils import utc_now


class UploadTask(BaseModel):
    __tablename__ = "upload_tasks"
    __table_args__ = (
        Index("idx_idempotency_key", "idempotency_key"),
        Index("idx_status", "status"),
        Index("idx_user_id", "user_id"),
        Index("idx_project_id", "project_id"),
        {"schema": "public"},
    )

    task_id = Column(UUID(as_uuid=True), primary_key=True)
    idempotency_key = Column(String, nullable=False)
    status = Column(task_status_enum, nullable=False, default=TaskStatus.PENDING)

    user_id = Column(UUID(as_uuid=True), ForeignKey("public.user.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("public.project.id"))

    file_hash = Column(String, nullable=True)
    task_metadata = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        onupdate=lambda: utc_now() + timedelta(hours=1),
        nullable=False,
    )

    user = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", back_populates="upload_tasks", foreign_keys=[project_id])
