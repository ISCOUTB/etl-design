from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import models, schemas
from src.core.config import settings
from src.core.security import decrypt_aegis256, encrypt_aegis256
from src.exceptions import (
    AppException,
    InvalidDBCredentialsException,
    ProjectAlreadyExistsException,
    ProjectHasActiveUsersException,
    ProjectNotFoundException,
)
from src.repositories import ProjectRepository
from src.services.parser import ParserService
from src.utils import create_postgres_uri


class ProjectService:
    def __init__(self, *, db: Session):
        self.repository = ProjectRepository(db=db)

    def __encrypt_db_credentials(
        self,
        project: models.Project,
        schema: schemas.CreateProjectSchema | schemas.UpdateProjectSchema,
    ) -> models.Project:
        fields = [
            "provider",
            "db_host",
            "db_port",
            "db_user",
            "db_password",
            "db_name",
            "db_params",
        ]
        for field in fields:
            value = getattr(schema, field, None)
            if value is not None:
                encrypted_value = encrypt_aegis256(
                    plaintext=str(value),
                    secret_key=settings.CREDENTIALS_SECRET_KEY,
                    secret_sign=settings.CREDENTIALS_SIGN,
                    project_id=str(project.id),
                    field_name=field,
                )
                setattr(project, field, encrypted_value)
            elif isinstance(schema, schemas.CreateProjectSchema):  # Value is None
                setattr(project, field, None)
            else:
                # Do nothing
                pass

        return project

    def __decrypt_db_credentials(self, project: models.Project) -> models.Project:
        fields = [
            "provider",
            "db_host",
            "db_port",
            "db_user",
            "db_password",
            "db_name",
            "db_params",
        ]
        for field in fields:
            value = getattr(project, field)
            if value and len(str(value)) > 32:
                try:
                    decrypted_value = decrypt_aegis256(
                        ciphertext_hex=str(value),
                        secret_key=settings.CREDENTIALS_SECRET_KEY,
                        secret_sign=settings.CREDENTIALS_SIGN,
                        project_id=str(project.id),
                        field_name=field,
                    )
                    setattr(project, field, decrypted_value)
                except ValueError:
                    continue

        return project

    def get_project_by_id(self, project_id: str) -> schemas.ResponseProjectSchema:
        project = self.repository.get_project_by_id(project_id)
        if project is None:
            raise ProjectNotFoundException()

        project = self.__decrypt_db_credentials(project)
        self.repository.db.expunge(project)
        return ParserService.parse_project(project)

    def get_project_db_uri(self, project_id: str) -> str:
        encrypted_project = self.repository.get_project_by_id(project_id)
        if encrypted_project is None:
            raise ProjectNotFoundException()

        project = self.__decrypt_db_credentials(encrypted_project)
        self.repository.db.expunge(project)
        print(project.name, project.db_user, project.db_password)
        try:
            return create_postgres_uri(
                user=project.db_user,  # type: ignore
                password=project.db_password,  # type: ignore
                host=project.db_host,  # type: ignore
                port=project.db_port,  # type: ignore
                db_name=project.db_name,  # type: ignore
            )
        except Exception:
            raise InvalidDBCredentialsException()

    def search_projects(
        self,
        name: Optional[str] = None,
        *,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[schemas.ResponseProjectSchema]:
        encrypted_projects = self.repository.search_projects(
            name=name, skip=skip, limit=limit
        )
        projects = list(map(self.__decrypt_db_credentials, encrypted_projects))
        for project in projects:
            self.repository.db.expunge(project)
        return ParserService.parse_projects(projects)

    def count_projects(self, name: Optional[str] = None) -> int:
        return self.repository.count_projects(name=name)

    def create_project(
        self, project_data: schemas.CreateProjectSchema
    ) -> schemas.ResponseProjectSchema:
        project = self.repository.create_project(project_data)
        print(project.id, project.name, project.db_user, project.db_password)
        try:
            self.repository.db.flush()  # Ensure project ID is generated before encryption
            project = self.__encrypt_db_credentials(project, project_data)
            print(project.id, project.name, project.db_user, project.db_password)
            self.repository.db.commit()
        except IntegrityError as e:
            self.repository.db.rollback()
            # Handle unique constraint violation for project name
            if "uq_project_name" in str(e.orig):
                raise ProjectAlreadyExistsException()
            else:
                raise AppException() from e
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        print(project.id, project.name, project.db_user, project.db_password)
        project = self.__decrypt_db_credentials(project)

        # Disassociate the object from the session to prevent autoflush from
        # saving plaintext values if there are subsequent DB operations
        self.repository.db.expunge(project)

        print(project.id, project.name, project.db_user, project.db_password)
        return ParserService.parse_project(project)

    def update_project(
        self,
        project_data: schemas.UpdateProjectSchema,
        *,
        project_id: str,
    ) -> schemas.ResponseProjectSchema:
        db_project = self.repository.get_project_by_id(project_id)
        if db_project is None:
            raise ProjectNotFoundException()

        updated_project = self.repository.update_project(
            project_data=project_data, db_project=db_project
        )

        try:
            updated_project = self.__encrypt_db_credentials(
                updated_project, schema=project_data
            )

            self.repository.db.commit()
        except IntegrityError as e:
            self.repository.db.rollback()
            # Handle unique constraint violation for project name
            if "uq_project_name" in str(e.orig):
                raise ProjectAlreadyExistsException()
            else:
                raise AppException() from e
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        updated_project = self.__decrypt_db_credentials(updated_project)
        self.repository.db.expunge(updated_project)
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
        self.repository.db.expunge(response.obj)
        return ParserService.parse_project(response.obj)
