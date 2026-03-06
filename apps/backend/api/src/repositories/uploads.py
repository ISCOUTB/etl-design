from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src import models, schemas
from src.core.config import settings
from src.utils import utc_now


class UploadRepository:
    def __init__(self, *, db: Session) -> None:
        self.db = db

    def create_upload_task(
        self,
        *,
        upload_task_create: schemas.UploadTaskCreateSchema,
        locked_until: Optional[datetime] = None,
    ) -> models.UploadTask:
        if locked_until is None:
            locked_until = utc_now() + timedelta(
                seconds=settings.IDEMPOTENCY_TTL_DEFAULT_SECONDS
            )

        upload_task = models.UploadTask(
            task_id=UUID(upload_task_create.task_id),
            idempotency_key=upload_task_create.idempotency_key,
            status=upload_task_create.status,
            user_id=UUID(upload_task_create.user_id),
            project_id=UUID(upload_task_create.project_id),
            file_hash=upload_task_create.file_hash,
            task_metadata=upload_task_create.task_metadata,
            locked_until=locked_until,
        )
        self.db.add(upload_task)
        self.db.flush()
        self.db.refresh(upload_task)
        return upload_task

    def get_upload_task_by_id(self, *, task_id: str) -> models.UploadTask | None:
        return (
            self.db.query(models.UploadTask)
            .filter(models.UploadTask.task_id == task_id)
            .first()
        )

    def update_upload_task_status(
        self,
        *,
        task_id: Optional[str] = None,
        status: models.TaskStatus,
        db_obj: Optional[models.UploadTask] = None,
    ) -> Optional[models.UploadTask]:
        if db_obj is None:
            assert task_id is not None, "Either task_id or db_obj must be provided"

            db_obj = self.get_upload_task_by_id(task_id=task_id)
            if db_obj is None:
                return None

        db_obj.status = status  # type: ignore
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def check_idempotency_task(
        self,
        *,
        idempotency_key: str,
        user_id: str,
        project_id: str,
        statuses: Optional[list[models.TaskStatus]] = None,
    ) -> Optional[models.UploadTask]:
        if statuses is None:
            statuses = [
                models.TaskStatus.PENDING,
                models.TaskStatus.PUBLISHED,
                models.TaskStatus.PROCESSING,
                models.TaskStatus.COMPLETED,
            ]

        task = (
            self.db.query(models.UploadTask)
            .filter(
                models.UploadTask.idempotency_key == idempotency_key,
                models.UploadTask.user_id == user_id,
                models.UploadTask.project_id == project_id,
                models.UploadTask.status.in_(statuses),
            )
            .order_by(models.UploadTask.created_at.desc())
            .first()
        )

        return task
