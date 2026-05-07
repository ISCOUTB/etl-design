from typing import List, Optional

from sqlalchemy import String, and_, cast
from sqlalchemy.orm import Session, aliased

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
        user_id: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[schemas.ProjectSearchRow]:
        owner_assignment = aliased(models.UserProject)
        owner_user = aliased(models.User)

        base_query = (
            self.db.query(
                models.Project,
                cast(owner_user.id, String).label("owner_id"),
                owner_user.name.label("owner_user"),
            )
            .outerjoin(
                owner_assignment,
                and_(
                    owner_assignment.project_id == models.Project.id,
                    owner_assignment.role == models.UserProjectType.OWNER,
                    owner_assignment.status == models.Status.ACTIVE,
                ),
            )
            .outerjoin(
                owner_user,
                and_(
                    owner_user.id == owner_assignment.user_id,
                    owner_user.status == models.Status.ACTIVE,
                ),
            )
        )

        if user_id is not None:
            assigned_user = aliased(models.UserProject)
            base_query = (
                base_query.join(
                    assigned_user,
                    assigned_user.project_id == models.Project.id,
                )
                .filter(assigned_user.user_id == user_id)
                .filter(assigned_user.status == models.Status.ACTIVE)
            )

        if name:
            base_query = base_query.filter(models.Project.name.ilike(f"{name}%"))

        base_query = base_query.distinct(models.Project.id)

        if skip is not None:
            base_query = base_query.offset(skip)

        if limit is not None:
            base_query = base_query.limit(limit)

        rows = base_query.all()
        return list(map(lambda row: (row[0], row[1], row[2]), rows))

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
            return user.status == models.Status.ACTIVE  # type: ignore

        return self._conditional_delete(
            models.Project,
            obj_id=project_id,
            relationship_attrs=["users"],
            filter_related_items=filter_active_users,
        )
