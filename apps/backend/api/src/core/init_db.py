from sqlalchemy.orm import Session

from src import models, schemas
from src.core.config import settings
from src.core.database_sql import SessionLocal
from src.repositories import UserRepository


def init_db(db: Session) -> None:
    repo = UserRepository(db=db)
    user_db = repo.get_by_email(settings.FIRST_SUPERUSER_EMAIL)
    if user_db is None:
        super_user_schema = schemas.CreateUserSchema(
            name=settings.FIRST_SUPERUSER_NAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            role=models.UserRole.SUDO,
        )
        repo.create_user(super_user_schema)
        db.commit()


if __name__ == "__main__":
    init_db(SessionLocal())
