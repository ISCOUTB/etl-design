from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas
from src.exceptions import AppException, UserProjectNotFoundException
from src.repositories.user_projects import UserProjectRepository
from src.services.parser import ParserService


class UserProjectService:
    def __init__(self, *, db: Session):
        self.db = db
        self.user_project_repo = UserProjectRepository(db=db)

    def get_owner_for_project(
        self, project_id: str
    ) -> schemas.ResponseUserProjectSchema:
        user_project = self.user_project_repo.get_owner_for_project(project_id)
        if user_project is None:
            raise UserProjectNotFoundException()

        return ParserService.parse_user_project(user_project)

    def get_user_type_for_project(
        self, user_id: str, project_id: str
    ) -> schemas.ResponseUserProjectSchema:
        user_project = self.user_project_repo.get_user_type_for_project(
            user_id, project_id
        )
        if user_project is None:
            raise UserProjectNotFoundException()

        return ParserService.parse_user_project(user_project)

    def get_projects_for_user(
        self,
        user_id: str,
        order_column: Optional[str] = None,
        asc: Optional[bool] = None,
    ) -> List[schemas.ResponseUserProjectSchema]:
        user_projects = self.user_project_repo.get_projects_for_user(
            user_id, order_column=order_column, asc=asc
        )
        return ParserService.parse_user_projects(user_projects)

    def get_users_for_project(
        self,
        project_id: str,
        role: Optional[models.UserProjectType] = None,
        order_column: Optional[str] = None,
        asc: Optional[bool] = None,
    ) -> List[schemas.ResponseUserProjectSchema]:
        user_projects = self.user_project_repo.get_users_for_project(
            project_id, role=role, order_column=order_column, asc=asc
        )
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

    def remove_user_from_project(self, user_id: str, project_id: str) -> None:
        db_user_project = self.user_project_repo.get_user_type_for_project(
            user_id=user_id, project_id=project_id
        )
        if not db_user_project:
            raise UserProjectNotFoundException()

        try:
            # If we're deleting the owner access, then we transfer the ownership
            # to the older user that accessed the project as SHARED,
            # if there are no more users with access to the project, then the project remains
            # orphaned until another user accesses it or an admin assigns an owner to it
            if db_user_project.role == models.UserProjectType.OWNER:
                users_in_project = self.user_project_repo.get_users_for_project(
                    project_id=project_id,
                    order_column="updated_at",
                    asc=False,
                    role=models.UserProjectType.SHARED,
                )
                if len(users_in_project) > 0:
                    retrieved_user_project = users_in_project[0]
                    self.user_project_repo.update_user_project(
                        db_user_project=retrieved_user_project,
                        update_data=schemas.UpdateUserProjectSchema(
                            role=models.UserProjectType.OWNER
                        ),
                    )

            self.user_project_repo.remove_user_from_project(
                db_user_project=db_user_project
            )
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise AppException() from e

    def flush_access_project(self, project_id: str) -> None:
        try:
            self.user_project_repo.flush_access_project(project_id=project_id)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise AppException() from e
