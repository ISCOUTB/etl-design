from typing import List, Optional

from sqlalchemy.orm import Session

from src import models, schemas
from src.core.security import get_password_hash
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    def __init__(self, *, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: str) -> Optional[models.User]:
        return self._get_by_id(models.User, obj_id=user_id)

    def search_users(
        self,
        active_only: bool = True,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[models.User]:
        base_query = self.db.query(models.User)
        if active_only:
            base_query = base_query.filter(
                models.User.status == models.UserStatus.ACTIVE
            )

        if name:
            base_query = base_query.filter(models.User.name.ilike(f"{name}%"))

        if email:
            base_query = base_query.filter(models.User.email.ilike(f"{email}%"))

        if skip is not None:
            base_query = base_query.offset(skip)

        if limit is not None:
            base_query = base_query.limit(limit)

        return base_query.all()

    def count_users(
        self,
        *,
        active_only: bool = True,
        name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> int:
        base_query = self.db.query(models.User)
        if active_only:
            base_query = base_query.filter(
                models.User.status == models.UserStatus.ACTIVE
            )

        if name:
            base_query = base_query.filter(models.User.name.ilike(f"{name}%"))

        if email:
            base_query = base_query.filter(models.User.email.ilike(f"{email}%"))

        return base_query.count()

    def create_user(self, user_data: schemas.CreateUserSchema) -> models.User:
        """Create a new user in the database."""
        hashed_password = get_password_hash(user_data.password)
        db_user = models.User(
            name=user_data.name,
            email=user_data.email,
            role=user_data.role,
            hashed_password=hashed_password,
        )
        self.db.add(db_user)
        return db_user

    def update_user(
        self,
        update_data: schemas.UpdateUserSchema,
        *,
        user_id: Optional[str] = None,
        db_user: Optional[models.User] = None,
    ) -> models.User:
        """Update an existing user's information."""
        return self._simple_update(
            models.User,
            obj_id=user_id,
            db_obj=db_user,
            update_data=update_data,
        )

    def delete_user(
        self, *, user_id: Optional[str] = None, db_user: Optional[models.User] = None
    ) -> schemas.DeleteResult[models.User]:
        """Delete a user from the database, only if they have no associated projects."""
        return self._conditional_delete(
            models.User,
            obj_id=user_id,
            db_obj=db_user,
            relationship_attrs=["projects"],
        )

    def inactivate_user(
        self,
        *,
        user_id: Optional[str] = None,
        db_user: Optional[models.User] = None,
    ) -> Optional[models.User]:
        """Inactivate a user by setting their status to INACTIVE.
        This is a soft delete that preserves the user's data and associations."""
        if db_user is None:
            assert user_id is not None, (
                "user_id must be provided if db_user is not given"
            )
            db_user = self.get_user_by_id(user_id)
            if not db_user:
                return None

        db_user.status = models.UserStatus.INACTIVE  # type: ignore
        self.db.flush()
        return db_user
