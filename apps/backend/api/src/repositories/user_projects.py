from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas
from src.repositories.base import BaseRepository


class UserProjectRepository(BaseRepository[models.UserProject]):
    def __init__(self, *, db: Session):
        self.db = db

    def get_projects_for_user(self, user_id: str) -> List[models.UserProject]:
        return (
            self.db.query(models.UserProject)
            .filter(models.UserProject.user_id == user_id)
            .all()
        )

    def get_users_for_project(self, project_id: str) -> List[models.UserProject]:
        return (
            self.db.query(models.UserProject)
            .filter(models.UserProject.project_id == project_id)
            .all()
        )

    def add_user_to_project(
        self, user_project_data: schemas.CreateUserProjectSchema
    ) -> models.UserProject:
        db_user_project = models.UserProject(
            user_id=user_project_data.user_id,
            project_id=user_project_data.project_id,
            role=user_project_data.role,
        )
        self.db.add(db_user_project)
        self.db.flush()
        return db_user_project

    def update_user_project(
        self,
        user_id: str,
        project_id: str,
        update_data: schemas.UpdateUserProjectSchema,
    ) -> Optional[models.UserProject]:
        db_user_project = (
            self.db.query(models.UserProject)
            .filter(
                models.UserProject.user_id == user_id,
                models.UserProject.project_id == project_id,
            )
            .first()
        )
        if not db_user_project:
            return None

        return self._simple_update(
            models.UserProject,
            obj_id=None,
            update_data=update_data,
            db_obj=db_user_project,
        )

    def remove_user_from_project(
        self, user_id: str, project_id: str
    ) -> schemas.DeleteResult[models.UserProject]:
        db_user_project = (
            self.db.query(models.UserProject)
            .filter(
                models.UserProject.user_id == user_id,
                models.UserProject.project_id == project_id,
            )
            .first()
        )
        if not db_user_project:
            return schemas.DeleteResult(success=False, status="not_found", obj=None)

        self.db.delete(db_user_project)
        self.db.flush()
        return schemas.DeleteResult(success=True, status="deleted", obj=db_user_project)
