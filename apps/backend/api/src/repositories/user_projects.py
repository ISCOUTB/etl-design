from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas
from src.repositories.base import BaseRepository


class UserProjectRepository(BaseRepository[models.UserProject]):
    def __init__(self, *, db: Session):
        self.db = db

    def get_owner_for_project(self, project_id: str) -> Optional[models.UserProject]:
        return (
            self.db.query(models.UserProject)
            .filter(
                models.UserProject.project_id == project_id,
                models.UserProject.role == models.UserProjectType.OWNER,
            )
            .first()
        )

    def get_user_type_for_project(
        self, user_id: str, project_id: str
    ) -> Optional[models.UserProject]:
        user_project = (
            self.db.query(models.UserProject)
            .filter(
                models.UserProject.project_id == project_id,
                models.UserProject.user_id == user_id,
            )
            .first()
        )
        return user_project

    def get_projects_for_user(
        self,
        user_id: str,
        order_column: Optional[str] = None,
        asc: Optional[bool] = None,
    ) -> List[models.UserProject]:
        base_query = self.db.query(models.UserProject).filter(
            models.UserProject.user_id == user_id
        )

        if order_column:
            asc = asc if asc is not None else True
            order_attr = getattr(models.UserProject, order_column, None)
            if order_attr is not None:
                if asc:
                    base_query = base_query.order_by(order_attr.asc())
                else:
                    base_query = base_query.order_by(order_attr.desc())

        return base_query.all()

    def get_users_for_project(
        self,
        project_id: str,
        role: Optional[models.UserProjectType] = None,
        order_column: Optional[str] = None,
        asc: Optional[bool] = None,
    ) -> List[models.UserProject]:
        base_query = self.db.query(models.UserProject).filter(
            models.UserProject.project_id == project_id
        )

        if role:
            base_query = base_query.filter(models.UserProject.role == role)

        if order_column:
            asc = asc if asc is not None else True
            order_attr = getattr(models.UserProject, order_column, None)
            if order_attr is not None:
                if asc:
                    base_query = base_query.order_by(order_attr.asc())
                else:
                    base_query = base_query.order_by(order_attr.desc())

        return base_query.all()

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
        *,
        update_data: schemas.UpdateUserProjectSchema,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        db_user_project: Optional[models.UserProject] = None,
    ) -> Optional[models.UserProject]:
        if db_user_project is None:
            assert user_id is not None and project_id is not None, (
                "Either db_user_project or both user_id and project_id must be provided"
            )
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
        self,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        db_user_project: Optional[models.UserProject] = None,
    ) -> schemas.DeleteResult[models.UserProject]:
        if db_user_project is None:
            assert user_id is not None and project_id is not None, (
                "Either db_user_project or both user_id and project_id must be provided"
            )
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

    def flush_access_project(self, project_id: str) -> None:
        # Flush all user-project associations for a project to force re-checking permissions
        self.db.query(models.UserProject).filter(
            models.UserProject.project_id == project_id,
            models.UserProject.role
            != models.UserProjectType.OWNER,  # Keep owners to avoid locking themselves out
        ).delete()
        self.db.flush()
        return None
