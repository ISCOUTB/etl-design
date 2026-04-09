from typing import Optional

from proto_utils.database import dtypes
from proto_utils.database.base_client import DatabaseClient
from sqlalchemy.orm import Session

from src import models, schemas
from src.exceptions import AppException, UploadTaskNotFoundException
from src.repositories import UploadRepository
from src.services.parser import ParserService


class UploadService:
    def __init__(self, *, db: Session):
        self.repository = UploadRepository(db=db)

    def get_upload_task_by_id(self, task_id: str) -> schemas.UploadTaskResponseSchema:
        task = self.repository.get_upload_task_by_id(task_id=task_id)
        if task is None:
            raise UploadTaskNotFoundException()

        return ParserService.parse_upload_task(task)

    def create_upload_task(
        self, upload_task_create: schemas.UploadTaskCreateSchema
    ) -> schemas.UploadTaskResponseSchema:
        try:
            task = self.repository.create_upload_task(
                upload_task_create=upload_task_create
            )
            self.repository.db.commit()
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        return ParserService.parse_upload_task(task)

    def update_upload_task_status(
        self,
        *,
        task_id: Optional[str] = None,
        status: schemas.UploadTaskUpdateSchema,
        db_obj: Optional[models.UploadTask] = None,
    ) -> schemas.UploadTaskResponseSchema:
        try:
            task = self.repository.update_upload_task_status(
                task_id=task_id, status=status.status, db_obj=db_obj
            )
            if task is None:
                raise UploadTaskNotFoundException()

            self.repository.db.commit()
        except UploadTaskNotFoundException:
            self.repository.db.rollback()
            raise
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        return ParserService.parse_upload_task(task)

    def check_idempotency_task(
        self,
        idempotency_key: str,
        user_id: str,
        project_id: str,
        db_client: DatabaseClient,
        upload_task: str,
    ) -> schemas.UploadTaskResponseSchema | None:
        cache_key = f"{upload_task}:idempotency:{idempotency_key}"
        try:
            cached_result = db_client.redis_get(dtypes.RedisGetRequest(key=cache_key))
            if cached_result["found"] and cached_result["value"] is not None:
                task_id = cached_result["value"]

                task = self.repository.get_upload_task_by_id(task_id=task_id)
                if task is not None:
                    return ParserService.parse_upload_task(task)
        except Exception:
            # Log the error but continue to check the database
            pass

        # Fall back to database check if cache miss or error
        exists, task = self.repository.check_idempotency_task(
            idempotency_key=idempotency_key, user_id=user_id, project_id=project_id
        )
        if not exists or task is None:
            return None

        # Log the hit
        try:
            db_client.redis_set(
                dtypes.RedisSetRequest(
                    key=cache_key,
                    value=str(task.task_id),
                    expiration=60 * 60 * 24,  # Cache for 1 day
                )
            )
        except Exception:
            # Log the error but do not fail the request
            pass

        return ParserService.parse_upload_task(task)
