from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas
from src.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[models.Project]):
    def __init__(self, *, db: Session):
        self.db = db

    def get_project_by_id(self, project_id: str) -> Optional[models.Project]:
        return self._get_by_id(models.Project, obj_id=project_id)

    def search_projects(
        self,
        name: Optional[str] = None,
        *,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[models.Project]:
        base_query = self.db.query(models.Project)
        if name:
            base_query = base_query.filter(models.Project.name.ilike(f"{name}%"))

        if skip is not None:
            base_query = base_query.offset(skip)

        if limit is not None:
            base_query = base_query.limit(limit)

        return base_query.all()

    def count_projects(self, name: Optional[str] = None) -> int:
        base_query = self.db.query(models.Project)
        if name:
            base_query = base_query.filter(models.Project.name.ilike(f"{name}%"))

        return base_query.count()

    def create_project(
        self, project_data: schemas.CreateProjectSchema
    ) -> models.Project:
        """Create a new project in the database."""
        db_project = models.Project(**project_data.model_dump(exclude_unset=True))
        self.db.add(db_project)
        return db_project

    def update_project(
        self,
        project_data: schemas.UpdateProjectSchema,
        *,
        project_id: Optional[str] = None,
        db_project: Optional[models.Project] = None,
    ) -> Optional[models.Project]:
        """Update an existing project with partial data."""
        return self._simple_update(
            models.Project,
            obj_id=project_id,
            update_data=project_data,
            db_obj=db_project,
        )

    def delete_project(
        self,
        *,
        project_id: str,
    ) -> schemas.DeleteResult[models.Project]:
        """Delete a project from the database, only if it has no associated users."""
        def filter_active_users(user: models.User) -> bool:
            return user.status == models.UserStatus.ACTIVE  # type: ignore

        return self._conditional_delete(
            models.Project,
            obj_id=project_id,
            relationship_attrs=["users"],
            filter_related_items=filter_active_users,
        )
