"""
Test factories for creating model instances with sensible defaults.

These factories provide a convenient way to create test data without
manually setting every field. They follow the Builder pattern and
can be customized per test.

Usage:
    user = UserFactory.create()  # User with defaults
    user = UserFactory.create(name="Alice")  # Override specific fields
    token = create_test_token(user_id="user-123")
"""

import uuid
from datetime import datetime, timedelta, timezone

from src import models, schemas
from src.services.auth import AuthService


class UserFactory:
    """Factory for creating User model instances for tests."""

    @staticmethod
    def create(**overrides) -> models.User:
        """
        Create a User instance with sensible defaults.

        Args:
            **overrides: Field values to override defaults

        Returns:
            models.User: A new user instance (not persisted)

        Example:
            user = UserFactory.create(name="Alice")
        """
        now = datetime.now(timezone.utc)
        defaults = {
            "id": uuid.uuid4(),
            "name": "Test User",
            "email": "test@example.com",
            "role": models.UserRole.USER,
            "status": models.Status.ACTIVE,
            "password": "hashed_password_here",
            "created_at": now,
            "updated_at": now,
        }
        defaults.update(overrides)
        return models.User(**defaults)


class ProjectFactory:
    """Factory for creating Project model instances for tests."""

    @staticmethod
    def create(**overrides) -> models.Project:
        """
        Create a Project instance with sensible defaults.

        Args:
            **overrides: Field values to override defaults

        Returns:
            models.Project: A new project instance (not persisted)

        Example:
            project = ProjectFactory.create(name="ETL Pipeline")
        """
        now = datetime.now(timezone.utc)
        defaults = {
            "id": uuid.uuid4(),
            "name": "Test Project",
            "status": models.Status.ACTIVE,
            "created_at": now,
        }
        defaults.update(overrides)
        return models.Project(**defaults)


class UserProjectFactory:
    """Factory for creating UserProject association instances for tests."""

    @staticmethod
    def create(**overrides) -> models.UserProject:
        """
        Create a UserProject instance with sensible defaults.

        Args:
            **overrides: Field values to override defaults

        Returns:
            models.UserProject: A new association instance (not persisted)

        Example:
            user_project = UserProjectFactory.create(
                user_id=user.id, project_id=project.id
            )
        """
        now = datetime.now(timezone.utc)
        defaults = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "project_id": uuid.uuid4(),
            "role": models.UserProjectType.OWNER,
            "created_at": now,
        }
        defaults.update(overrides)
        return models.UserProject(**defaults)


# ============================================================================
# Token Helpers
# ============================================================================


def create_test_token(
    user_id: str,
    expire_seconds: int = 3600,
    role: models.UserRole = models.UserRole.USER,
    name: str = "Test User",
    email: str = "test@example.com",
) -> str:
    """
    Create a valid JWT token for testing authenticated endpoints.

    Args:
        user_id: The user ID to encode in the token
        expire_seconds: How long until token expires (default 1 hour)
        role: Role to encode in token
        name: User display name in token payload
        email: User email in token payload

    Returns:
        str: A valid JWT token that can be used in Authorization header

    Example:
        token = create_test_token("user-123")
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/me", headers=headers)
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=expire_seconds)

    payload = schemas.TokenPayload(
        id=user_id,
        name=name,
        email=email,
        sub=user_id,
        role=role,
        exp=int(exp.timestamp()),
        iat=int(now.timestamp()),
        jti=str(uuid.uuid4()),
    )

    return AuthService.encode_access_token(payload)
