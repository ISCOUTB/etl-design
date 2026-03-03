from datetime import timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src import models, schemas
from src.utils import utc_now


class UploadRepository:
    def __init__(self, *, db: Session) -> None:
        self.db = db

    def create_upload_task(
        self, *, upload_task_create: schemas.UploadTaskCreateSchema
    ) -> models.UploadTask:
        upload_task = models.UploadTask(
            task_id=UUID(upload_task_create.task_id),  # type: ignore
            idempotency_key=upload_task_create.idempotency_key,  # type: ignore
            status=upload_task_create.status,  # type: ignore
            user_id=UUID(upload_task_create.user_id),  # type: ignore
            project_id=UUID(upload_task_create.project_id),  # type: ignore
            file_hash=upload_task_create.file_hash,  # type: ignore
            task_metadata=upload_task_create.task_metadata,  # type: ignore
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
    ) -> models.UploadTask | None:
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
        self, *, idempotency_key: str, user_id: str, project_id: str
    ) -> Tuple[bool, models.UploadTask | None]:
        task = (
            self.db.query(models.UploadTask)
            .filter(
                models.UploadTask.idempotency_key == idempotency_key,
                models.UploadTask.user_id == user_id,
                models.UploadTask.project_id == project_id,
                models.UploadTask.created_at > utc_now() - timedelta(days=30),
                models.UploadTask.status.in_(
                    [
                        models.TaskStatus.PENDING.name,
                        models.TaskStatus.PUBLISHED.name,
                        models.TaskStatus.PROCESSING.name,
                        models.TaskStatus.COMPLETED.name,
                    ]
                ),
            )
            .order_by(models.UploadTask.created_at.desc())
            .first()
        )

        return task is not None, task
