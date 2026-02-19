from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import models, schemas
from src.exceptions import (
    ProjectAlreadyExistsException,
    ProjectHasActiveUsersException,
    ProjectNotFoundException,
)
from src.repositories import ProjectRepository
from src.services.parser import ParserService


class ProjectService:
    def __init__(self, *, db: Session):
        self.repository = ProjectRepository(db=db)

    def get_project_by_id(self, project_id: str) -> schemas.ResponseProjectSchema:
        project = self.repository.get_project_by_id(project_id)
        if project is None:
            raise ProjectNotFoundException()

        return ParserService.parse_project(project)

    def search_projects(
        self,
        name: Optional[str] = None,
        *,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[schemas.ResponseProjectSchema]:
        projects = self.repository.search_projects(name=name, skip=skip, limit=limit)
        return ParserService.parse_projects(projects)

    def count_projects(self, name: Optional[str] = None) -> int:
        return self.repository.count_projects(name=name)

    def create_project(
        self, project_data: schemas.CreateProjectSchema
    ) -> schemas.ResponseProjectSchema:
        project = self.repository.create_project(project_data)
        try:
            self.repository.db.commit()
        except IntegrityError as e:
            # Handle unique constraint violation for project name
            if "uq_project_name" in str(e.orig):
                raise ProjectAlreadyExistsException()

        return ParserService.parse_project(project)

    def update_project(
        self,
        project_data: schemas.UpdateProjectSchema,
        *,
        project_id: Optional[str] = None,
        db_project: Optional[models.Project] = None,
    ) -> schemas.ResponseProjectSchema:
        updated_project = self.repository.update_project(
            project_data=project_data, project_id=project_id, db_project=db_project
        )
        if updated_project is None:
            raise ProjectNotFoundException()

        try:
            self.repository.db.commit()
        except IntegrityError as e:
            # Handle unique constraint violation for project name
            if "uq_project_name" in str(e.orig):
                raise ProjectAlreadyExistsException()

        return ParserService.parse_project(updated_project)

    def delete_project(self, project_id: str) -> schemas.ResponseProjectSchema:
        response = self.repository.delete_project(project_id=project_id)
        if not response.success:
            if response.status == "not_found":
                raise ProjectNotFoundException()

            if response.status == "has_dependencies":
                raise ProjectHasActiveUsersException()
            
        assert response.obj is not None, (
            "Deleted project object should be returned on successful deletion"
        )
        return ParserService.parse_project(response.obj)
