# TODO: Change the print statements for a logger

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple

import grpc
from fastapi import UploadFile
from messaging_utils.core.config import settings as mq_settings
from messaging_utils.messaging.publishers import Publisher
from messaging_utils.schemas import Metadata
from pika.exceptions import AMQPError
from proto_utils.database import dtypes
from proto_utils.database.base_client import DatabaseClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from uuidv7 import uuid7

from src import models, schemas
from src.core.config import settings
from src.core.constants import INSERTION_TASK, VALIDATION_TASK
from src.exceptions import (
    AppException,
    ContentTypeEmptyException,
    FileContentEmptyException,
    FilenameEmptyException,
)
from src.repositories import UploadRepository
from src.utils import utc_now


class IdempotencyService:
    def __init__(self, *, db: Session) -> None:
        self.upload_repository = UploadRepository(db=db)

    @staticmethod
    def _generate_idempotency_key(
        user_id: str,
        project_id: str,
        table_name: str,
        file_hash: str,
        metadata: Optional[str] = None,
        current_timestamp: Optional[datetime] = None,
    ) -> str:
        """Generate deterministic idempotency key from file and context."""
        if current_timestamp is None:
            current_timestamp = utc_now()

        data = f"{user_id}:{project_id}:{table_name}:{file_hash}"
        if metadata:
            data += f":{metadata}"

        return hashlib.sha256(data.encode()).hexdigest()

    def validate_idempotency_key(
        self,
        *,
        user_id: str,
        project_id: str,
        idempotency_key: str,
    ) -> Tuple[bool, models.UploadTask | None]:
        is_duplicate, task = self.upload_repository.check_idempotency_task(
            idempotency_key=idempotency_key,
            user_id=user_id,
            project_id=project_id,
        )

        if not is_duplicate or task is None:
            return False, None

        ttl_seconds = settings.IDEMPOTENCY_KEY_EXPIRATION_SECONDS

        task_creation = task.created_at
        is_expired = bool(task_creation < (utc_now() - timedelta(seconds=ttl_seconds)))
        return (not is_expired), task

    async def validate_task(
        self,
        db_client: DatabaseClient,
        publisher: Publisher,
        *,
        spreadsheet_file: UploadFile,
        user_id: str,
        project_id: str,
        table_name: str,
    ) -> dtypes.ApiResponse:
        file_content = await spreadsheet_file.read()
        if not file_content:
            raise FileContentEmptyException()

        if not spreadsheet_file.filename:
            raise FilenameEmptyException()

        if not spreadsheet_file.content_type:
            raise ContentTypeEmptyException()

        file_hash = hashlib.sha256(file_content).hexdigest()
        idempotency_key = self._generate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            table_name=table_name,
            file_hash=file_hash,
            metadata=VALIDATION_TASK,
        )
        is_duplicate, existing_task = self.validate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
        )

        if is_duplicate and existing_task is not None:
            try:
                existing_response = db_client.get_task_id(
                    dtypes.GetTaskIdRequest(
                        task=VALIDATION_TASK, task_id=str(existing_task.task_id)
                    )
                )
                if (
                    existing_response["found"]
                    and existing_response["value"] is not None
                ):
                    response = existing_response["value"]
                    if response["status"] in {
                        models.TaskStatus.PENDING.value,
                        models.TaskStatus.PUBLISHED.value,
                    }:
                        response["status"] = existing_task.status.value
                        response["message"] = "This validation is already in progress"
                        response["code"] = 202

                    return response
            except Exception as e:
                print(
                    "Error fetching existing task from cache, returning database status",
                    e,
                )

            return dtypes.ApiResponse(
                status=existing_task.status.value,
                code=202,  # Still processing
                message="This validation is already in progress",
                data={
                    "task_id": str(existing_task.task_id),
                    "project_id": project_id,
                    "idempotency_key": idempotency_key,
                },
            )

        task_id = str(uuid7())

        # Create Metadata object obtained from the uploaded file
        metadata = Metadata(
            filename=spreadsheet_file.filename,
            content_type=spreadsheet_file.content_type,
            size=len(file_content),
        )

        # First, create the task in Redis and in our database with status "pending"
        try:
            # Save the task in the database with status "pending"
            db_task = self.upload_repository.create_upload_task(
                upload_task_create=schemas.UploadTaskCreateSchema(
                    task_id=task_id,
                    idempotency_key=idempotency_key,
                    status=models.TaskStatus.PENDING,  # type: ignore
                    user_id=user_id,
                    project_id=project_id,
                    file_hash=file_hash,
                    task_metadata=metadata,
                )
            )

            # Set the task ID in Redis with the appropriate key and value
            db_client.set_task_id(
                dtypes.SetTaskIdRequest(
                    task_id=task_id,
                    value=dtypes.ApiResponse(
                        status=models.TaskStatus.PENDING.value,
                        code=202,
                        message="Validation request created successfully",
                        data={"task_id": task_id, "project_id": project_id},
                    ),
                    task=VALIDATION_TASK,
                )
            )
            self.upload_repository.db.commit()
        except grpc.RpcError as e:
            # If it's a grpc problem, then it's neccesary make a roll back, and raise the same exception
            # the grpc_exception_handler will manage this exception and return the appropriate response,
            # so we can just raise the same error.
            print("gRPC error occurred, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise
        except OperationalError as e:
            # If the problem is the postgres database, that means, we should roll back the transaction,
            # update the cache to remove the pending task, and raise an AppException.
            print("Database operation failed, rolling back task creation", e)

            # TODO: Use the `db_client` to remove a task
            self.upload_repository.db.rollback()
            raise AppException() from e
        except Exception as e:
            print("Failed to create upload task, rolling back", e)

            # TODO: use the `db_client` to remove a task
            self.upload_repository.db.rollback()
            raise AppException() from e

        # Second, publish the task to rabbitmq broker
        try:
            # Update the status to published
            db_task.status = models.TaskStatus.PUBLISHED  # type: ignore

            # Publish in RabbitMQ
            publisher.publish_validation_request(
                routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_VALIDATIONS,
                file_data=file_content,
                project_id=project_id,
                table_name=table_name,
                metadata=metadata,
                task="sample_validation",
                task_id=task_id,
                idempotency_key=idempotency_key,
            )

            self.upload_repository.db.commit()
        except OperationalError as e:
            print("Database operation failed, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise AppException() from e
        except AMQPError as e:
            print("Failed to publish validation request, rolling back task creation", e)
            self.upload_repository.db.rollback()

            # The rabbitmq_exception_handler manages this error, so we can just raise the same error
            raise
        except Exception as e:
            print("Failed to publish validation request, rolling back task creation", e)
            raise AppException() from e

        return dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation request published successfully",
            data={"task_id": task_id, "project_id": project_id},
        )

    async def insert_task(
        self,
        db_client: DatabaseClient,
        publisher: Publisher,
        *,
        spreadsheet_file: UploadFile,
        user_id: str,
        project_id: str,
        table_name: str,
        db_uri: str,
        overwrite: bool = False,
    ) -> dtypes.ApiResponse:
        file_content = await spreadsheet_file.read()
        if not file_content:
            raise FileContentEmptyException()

        if not spreadsheet_file.filename:
            raise FilenameEmptyException()

        if not spreadsheet_file.content_type:
            raise ContentTypeEmptyException()

        file_hash = hashlib.sha256(file_content).hexdigest()
        idempotency_key = self._generate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            table_name=table_name,
            file_hash=file_hash,
            metadata=INSERTION_TASK,
        )
        is_duplicate, existing_task = self.validate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
        )

        if is_duplicate and existing_task is not None:
            try:
                existing_response = db_client.get_task_id(
                    dtypes.GetTaskIdRequest(
                        task=VALIDATION_TASK, task_id=str(existing_task.task_id)
                    )
                )
                if (
                    existing_response["found"]
                    and existing_response["value"] is not None
                ):
                    response = existing_response["value"]
                    if response["status"] in {
                        models.TaskStatus.PENDING.value,
                        models.TaskStatus.PUBLISHED.value,
                    }:
                        response["status"] = existing_task.status.value
                        response["message"] = "This validation is already in progress"
                        response["code"] = 202

                    return response
            except Exception as e:
                print(
                    "Error fetching existing task from cache, returning database status",
                    e,
                )

        task_id = str(uuid7())

        metadata = Metadata(
            filename=spreadsheet_file.filename,
            content_type=spreadsheet_file.content_type,
            size=len(file_content),
        )

        try:
            db_task = self.upload_repository.create_upload_task(
                upload_task_create=schemas.UploadTaskCreateSchema(
                    task_id=task_id,
                    idempotency_key=idempotency_key,
                    status=models.TaskStatus.PENDING,  # type: ignore
                    user_id=user_id,
                    project_id=project_id,
                    file_hash=file_hash,
                    task_metadata=metadata,
                )
            )

            db_client.set_task_id(
                dtypes.SetTaskIdRequest(
                    task_id=task_id,
                    value=dtypes.ApiResponse(
                        status=models.TaskStatus.PENDING.value,
                        code=202,
                        message="Insertion request created successfully",
                        data={"task_id": task_id, "project_id": project_id},
                    ),
                    task=INSERTION_TASK,
                )
            )
            self.upload_repository.db.commit()
        except grpc.RpcError as e:
            print("gRPC error occurred, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise
        except OperationalError as e:
            print("Database operation failed, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise AppException() from e
        except Exception as e:
            print("Failed to create upload task, rolling back", e)
            self.upload_repository.db.rollback()
            raise AppException() from e

        try:
            db_task.status = models.TaskStatus.PUBLISHED  # type: ignore

            publisher.publish_insertion_request(
                routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_INSERTION,
                file_data=file_content,
                project_id=project_id,
                table_name=table_name,
                metadata=metadata,
                task="sample_insertion",
                overwrite=overwrite,
                db_uri=db_uri,
                task_id=task_id,
                idempotency_key=idempotency_key,
            )

            self.upload_repository.db.commit()
        except OperationalError as e:
            print("Database operation failed, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise AppException() from e
        except AMQPError as e:
            print("Failed to publish insertion request, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise
        except Exception as e:
            print("Failed to publish insertion request, rolling back task creation", e)
            raise AppException() from e

        return dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Insertion request published successfully",
            data={"task_id": task_id, "project_id": project_id},
        )

    async def process_task(
        self,
        db_client: DatabaseClient,
        publisher: Publisher,
        *,
        spreadsheet_file: UploadFile,
        user_id: str,
        project_id: str,
        table_name: str,
        db_uri: str,
        overwrite: bool = False,
    ) -> dtypes.ApiResponse:
        file_content = await spreadsheet_file.read()
        if not file_content:
            raise FileContentEmptyException()

        if not spreadsheet_file.filename:
            raise FilenameEmptyException()

        if not spreadsheet_file.content_type:
            raise ContentTypeEmptyException()

        file_hash = hashlib.sha256(file_content).hexdigest()
        idempotency_key = self._generate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            table_name=table_name,
            file_hash=file_hash,
            metadata=VALIDATION_TASK,
        )
        is_duplicate, existing_task = self.validate_idempotency_key(
            user_id=user_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
        )

        if is_duplicate and existing_task is not None:
            try:
                existing_response = db_client.get_task_id(
                    dtypes.GetTaskIdRequest(
                        task=VALIDATION_TASK, task_id=str(existing_task.task_id)
                    )
                )
                if (
                    existing_response["found"]
                    and existing_response["value"] is not None
                ):
                    response = existing_response["value"]
                    if response["status"] in {
                        models.TaskStatus.PENDING.value,
                        models.TaskStatus.PUBLISHED.value,
                    }:
                        response["status"] = existing_task.status.value
                        response["message"] = "This validation is already in progress"
                        response["code"] = 202

                    return response
            except Exception as e:
                print(
                    "Error fetching existing task from cache, returning database status",
                    e,
                )

        task_id = str(uuid7())
        metadata = Metadata(
            filename=spreadsheet_file.filename,
            content_type=spreadsheet_file.content_type,
            size=len(file_content),
        )

        try:
            db_task = self.upload_repository.create_upload_task(
                upload_task_create=schemas.UploadTaskCreateSchema(
                    task_id=task_id,
                    idempotency_key=idempotency_key,
                    status=models.TaskStatus.PENDING,  # type: ignore
                    user_id=user_id,
                    project_id=project_id,
                    file_hash=file_hash,
                    task_metadata=metadata,
                )
            )

            db_client.set_task_id(
                dtypes.SetTaskIdRequest(
                    task_id=task_id,
                    value=dtypes.ApiResponse(
                        status=models.TaskStatus.PENDING.value,
                        code=202,
                        message="Validation/Insertion request created successfully",
                        data={"task_id": task_id, "project_id": project_id},
                    ),
                    task=VALIDATION_TASK,
                )
            )
            self.upload_repository.db.commit()
        except grpc.RpcError as e:
            print("gRPC error occurred, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise
        except OperationalError as e:
            print("Database operation failed, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise AppException() from e
        except Exception as e:
            print("Failed to create upload task, rolling back", e)
            self.upload_repository.db.rollback()
            raise AppException() from e

        try:
            db_task.status = models.TaskStatus.PUBLISHED  # type: ignore
            publisher.publish_validation_request(
                routing_key=mq_settings.RABBITMQ_PUBLISHERS_ROUTING_KEY_VALIDATIONS,
                file_data=file_content,
                project_id=project_id,
                table_name=table_name,
                metadata=metadata,
                task="sample_validation",
                insert=True,
                insert_overwrite=overwrite,
                insert_db_uri=db_uri,
                task_id=task_id,
                idempotency_key=idempotency_key,
            )

            self.upload_repository.db.commit()
        except OperationalError as e:
            print("Database operation failed, rolling back task creation", e)
            self.upload_repository.db.rollback()
            raise AppException() from e
        except AMQPError as e:
            print(
                "Failed to publish validation/insertion request, rolling back task creation",
                e,
            )
            self.upload_repository.db.rollback()
            raise
        except Exception as e:
            print(
                "Failed to publish validation/insertion request, rolling back task creation",
                e,
            )
            raise AppException() from e

        return dtypes.ApiResponse(
            status="accepted",
            code=202,
            message="Validation/Insertion request published successfully",
            data={"task_id": task_id, "project_id": project_id},
        )
