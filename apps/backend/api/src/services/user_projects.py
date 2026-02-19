from typing import List

from sqlalchemy.orm import Session

from src import models, schemas
from src.exceptions import AppException, UserProjectNotFoundException
from src.repositories.user_projects import UserProjectRepository
from src.services.parser import ParserService


class UserProjectService:
    def __init__(self, *, db: Session):
        self.db = db
        self.user_project_repo = UserProjectRepository(db=db)

    def get_projects_for_user(
        self, user_id: str
    ) -> List[schemas.ResponseUserProjectSchema]:
        user_projects = self.user_project_repo.get_projects_for_user(user_id)
        return ParserService.parse_user_projects(user_projects)

    def get_users_for_project(
        self, project_id: str
    ) -> List[schemas.ResponseUserProjectSchema]:
        user_projects = self.user_project_repo.get_users_for_project(project_id)
        return ParserService.parse_user_projects(user_projects)

    def add_user_to_project(
        self, user_project_data: schemas.CreateUserProjectSchema
    ) -> schemas.ResponseUserProjectSchema:
        db_user_project = self.user_project_repo.add_user_to_project(
            user_project_data=user_project_data
        )
        self.db.commit()
        return ParserService.parse_user_project(db_user_project)

    def update_user_project(
        self,
        user_id: str,
        project_id: str,
        update_data: schemas.UpdateUserProjectSchema,
    ) -> schemas.ResponseUserProjectSchema:
        db_user_project = self.user_project_repo.update_user_project(
            user_id=user_id, project_id=project_id, update_data=update_data
        )
        if not db_user_project:
            raise UserProjectNotFoundException()

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise AppException() from e

        return ParserService.parse_user_project(db_user_project)

    def remove_user_from_project(
        self, user_id: str, project_id: str, role: models.UserProjectType
    ) -> None:
        db_user_project = self.user_project_repo.update_user_project(
            user_id=user_id,
            project_id=project_id,
            update_data=schemas.UpdateUserProjectSchema(role=role),
        )
        if not db_user_project:
            raise UserProjectNotFoundException()

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise AppException() from e
