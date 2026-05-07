# type: ignore

from typing import List, Optional

from src import models, schemas
from src.core.constants import DEFAULT_OWNER_ID, DEFAULT_OWNER_USER


class ParserService:
    @staticmethod
    def parse_user(user: models.User) -> schemas.ResponseUserSchema:
        return schemas.ResponseUserSchema(
            id=str(user.id),
            name=str(user.name),
            email=str(user.email),
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def parse_users(users: List[models.User]) -> List[schemas.ResponseUserSchema]:
        return list(map(ParserService.parse_user, users))

    @staticmethod
    def parse_project(
        project: models.Project,
        *,
        owner_id: Optional[str] = None,
        owner_user: Optional[str] = None,
    ) -> schemas.ResponseProjectSchema:
        return schemas.ResponseProjectSchema(
            id=str(project.id),
            name=str(project.name),
            provider=project.provider,
            db_host=project.db_host,
            db_port=project.db_port,
            db_user=project.db_user,
            db_password=project.db_password,
            db_name=project.db_name,
            db_params=project.db_params,
            description=project.description,
            owner_id=owner_id or DEFAULT_OWNER_ID,
            owner_user=owner_user or DEFAULT_OWNER_USER,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    def parse_projects(
        projects: List[models.Project],
    ) -> List[schemas.ResponseProjectSchema]:
        return list(map(ParserService.parse_project, projects))

    @staticmethod
    def parse_user_project(
        user_project: models.UserProject,
    ) -> schemas.ResponseUserProjectSchema:
        return schemas.ResponseUserProjectSchema(
            user_id=str(user_project.user_id),
            project_id=str(user_project.project_id),
            role=user_project.role,
            status=user_project.status,
            created_at=user_project.created_at,
            updated_at=user_project.updated_at,
        )

    @staticmethod
    def parse_user_projects(
        user_projects: List[models.UserProject],
    ) -> List[schemas.ResponseUserProjectSchema]:
        return list(map(ParserService.parse_user_project, user_projects))

    @staticmethod
    def parse_upload_task(
        upload_task: models.UploadTask,
    ) -> schemas.UploadTaskResponseSchema:
        return schemas.UploadTaskResponseSchema(
            task_id=str(upload_task.task_id),
            idempotency_key=str(upload_task.idempotency_key),
            status=upload_task.status,
            user_id=str(upload_task.user_id),
            project_id=str(upload_task.project_id),
            file_hash=upload_task.file_hash,
            task_metadata=upload_task.task_metadata,
            created_at=upload_task.created_at,
            updated_at=upload_task.updated_at,
        )
