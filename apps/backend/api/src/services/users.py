from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import models, schemas
from src.core.security import get_password_hash
from src.exceptions import (
    AppException,
    EmailFormatException,
    EmailInUseException,
    UserHasActiveProjectsException,
    UserNotFoundException,
)
from src.repositories import UserRepository
from src.services.parser import ParserService


class UserService:
    def __init__(self, *, db: Session):
        self.repository = UserRepository(db=db)

    def get_user_by_id(self, user_id: str) -> schemas.ResponseUserSchema:
        user = self.repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException()

        return ParserService.parse_user(user)

    def get_user_by_email(self, email: str) -> schemas.ResponseUserSchema:
        user = self.repository.get_by_email(email)
        if user is None:
            raise UserNotFoundException()

        return ParserService.parse_user(user)

    def search_users(
        self,
        active_only: bool = True,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[models.UserRole] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[schemas.ResponseUserSchema]:
        users = self.repository.search_users(
            active_only=active_only,
            name=name,
            email=email,
            role=role,
            skip=skip,
            limit=limit,
        )
        return ParserService.parse_users(users)

    def count_users(
        self,
        *,
        active_only: bool = True,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[models.UserRole] = None,
    ) -> int:
        return self.repository.count_users(
            active_only=active_only, name=name, email=email, role=role
        )

    def create_user(
        self, user_data: schemas.CreateUserSchema
    ) -> schemas.ResponseUserSchema:
        user = self.repository.create_user(user_data)
        try:
            self.repository.db.commit()
        except IntegrityError as e:
            self.repository.db.rollback()
            if "uq_user_email" in str(e.orig):
                raise EmailInUseException()
            elif "ck_user_email_format" in str(e.orig):
                raise EmailFormatException()
            else:
                raise AppException() from e

        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        return ParserService.parse_user(user)

    def update_user(
        self, user_id: str, update_data: schemas.UpdateUserSchema
    ) -> schemas.ResponseUserSchema:
        db_user = self.repository.get_user_by_id(user_id)
        if db_user is None:
            raise UserNotFoundException()

        if update_data.password is not None:
            update_data.password = get_password_hash(update_data.password)

        user = self.repository.update_user(update_data, db_user=db_user)
        try:
            self.repository.db.commit()
        except IntegrityError as e:
            self.repository.db.rollback()
            if "uq_user_email" in str(e.orig):
                raise EmailInUseException()
            elif "ck_user_email_format" in str(e.orig):
                raise EmailFormatException()
            else:
                raise AppException() from e
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        return ParserService.parse_user(user)

    def delete_user(self, user_id: str) -> schemas.ResponseUserSchema:
        db_user = self.repository.get_user_by_id(user_id)
        if db_user is None:
            raise UserNotFoundException()

        match db_user.status:
            case models.UserStatus.ACTIVE:
                response = self.repository.inactivate_user(db_user=db_user)
            case models.UserStatus.INACTIVE:
                response = self.repository.delete_user(db_user=db_user)
            case _:
                raise AppException("Invalid user status")

        try:
            self.repository.db.commit()
        except Exception as e:
            self.repository.db.rollback()
            raise AppException() from e

        # This should never happens, the db_user is never None at this point,
        # but we need to satisfy the type checker
        if response is None:
            raise UserNotFoundException()

        if isinstance(response, models.User):
            return ParserService.parse_user(response)

        # isinstance(response, DeleteResult[models.User])
        if not response.success:
            if response.status == "not_found":
                raise UserNotFoundException()

            if response.status == "has_dependencies":
                raise UserHasActiveProjectsException()

        assert response.obj is not None, (
            "Deleted user object should be returned on successful deletion"
        )
        return ParserService.parse_user(response.obj)
