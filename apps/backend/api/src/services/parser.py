# type: ignore

from typing import List

from src import models, schemas


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
    def parse_project(project: models.Project) -> schemas.ResponseProjectSchema:
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
            created_at=user_project.created_at,
            updated_at=user_project.updated_at,
        )

    @staticmethod
    def parse_user_projects(
        user_projects: List[models.UserProject],
    ) -> List[schemas.ResponseUserProjectSchema]:
        return list(map(ParserService.parse_user_project, user_projects))
