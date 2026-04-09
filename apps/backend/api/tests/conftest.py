# type: ignore
"""
Centralized pytest fixtures for ETL Design API tests.

This module provides database sessions with automatic rollback, repository instances,
service instances with mocked databases, and utility fixtures for comprehensive testing.

Database Strategy:
- Repositories: Use real database connection with transaction rollback for test isolation
- Services: Use mocked database to test business logic without side effects
- Fixtures are function-scoped to ensure clean state for each test
"""

import uuid
from typing import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from src import models, schemas
from src.api.deps import get_sql_db
from src.core.database_sql import engine
from src.main import app
from src.repositories import (
    ProjectRepository,
    UploadRepository,
    UserProjectRepository,
    UserRepository,
)
from src.services import (
    AuthService,
    ProjectService,
    UploadService,
    UserProjectService,
    UserService,
)
from tests.utils.factories import create_test_token


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Provide a SQLAlchemy session with automatic transaction rollback.

    This fixture creates a new database connection and transaction for each test.
    After the test completes, all changes are rolled back, ensuring a clean state
    for the next test without requiring manual cleanup or database seeding.

    Implements savepoint/nested transaction pattern to properly handle SQLAlchemy's
    after_transaction_end event, which is crucial for test isolation.

    Yields:
        Session: SQLAlchemy session bound to a transaction that will be rolled back

    Example:
        def test_create_user(db: Session):
            user = User(name="Test User", email="test@example.com")
            db.add(user)
            db.commit()
            # User exists in this test
            # User is rolled back after test completes
    """
    connection = engine.connect()
    txn = connection.begin()
    session = Session(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session: Session, transaction):
        """Restart savepoint to enable proper nested transactions."""
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()
        if txn.is_active:
            txn.rollback()
        connection.close()


@pytest.fixture(scope="function")
def mock_db() -> Mock:
    """
    Provide a mocked SQLAlchemy session for service testing.

    This mock avoids database operations during service tests, allowing
    focus on business logic without side effects. Services initialized
    with this mock should have their repository methods mocked as well.

    Returns:
        Mock: A mock object with commit/rollback/flush methods

    Example:
        def test_user_service_validation(mock_db: Mock):
            service = UserService(db=mock_db)
            # Test business logic without touching the database
    """
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.flush = Mock()
    db.add = Mock()
    db.query = Mock()
    return db


# ============================================================================
# Repository Fixtures - Use Real Database
# ============================================================================
# These fixtures provide repository instances with real database access.
# They are used to test data access layer logic with proper transaction
# management and constraint validation.


@pytest.fixture(scope="function")
def user_repo(db: Session) -> UserRepository:
    """Provide a UserRepository instance connected to test database."""
    return UserRepository(db=db)


@pytest.fixture(scope="function")
def project_repo(db: Session) -> ProjectRepository:
    """Provide a ProjectRepository instance connected to test database."""
    return ProjectRepository(db=db)


@pytest.fixture(scope="function")
def upload_repo(db: Session) -> UploadRepository:
    """Provide an UploadRepository instance connected to test database."""
    return UploadRepository(db=db)


@pytest.fixture(scope="function")
def user_project_repo(db: Session) -> UserProjectRepository:
    """Provide a UserProjectRepository instance connected to test database."""
    return UserProjectRepository(db=db)


# ============================================================================
# Service Fixtures - Use Mocked Database
# ============================================================================
# These fixtures provide service instances with mocked database connections.
# They are used to test business logic without affecting the database.
# Individual repository methods should be mocked in tests as needed.


@pytest.fixture(scope="function")
def user_service(mock_db: Mock) -> UserService:
    """Create UserService instance with mocked database."""
    return UserService(db=mock_db)


@pytest.fixture(scope="function")
def project_service(mock_db: Mock) -> ProjectService:
    """Create ProjectService instance with mocked database."""
    return ProjectService(db=mock_db)


@pytest.fixture(scope="function")
def upload_service(mock_db: Mock) -> UploadService:
    """Create UploadService instance with mocked database."""
    return UploadService(db=mock_db)


@pytest.fixture(scope="function")
def user_project_service(mock_db: Mock) -> UserProjectService:
    """Create UserProjectService instance with mocked database."""
    return UserProjectService(db=mock_db)


@pytest.fixture(scope="function")
def auth_service(mock_db: Mock) -> AuthService:
    """Create AuthService instance with mocked database."""
    return AuthService(db=mock_db)


# ============================================================================
# Authentication & User Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_user(db: Session, user_repo: UserRepository):
    """
    Create a test user in the database for authenticated endpoint testing.

    Returns:
        models.User: A user instance persisted in the test database

    Example:
        def test_get_current_user(test_client, test_user, test_token):
            headers = {"Authorization": f"Bearer {test_token}"}
            response = test_client.get("/api/v1/users/me", headers=headers)
            assert response.json()["id"] == str(test_user.id)
    """
    # This user is committed to be visible from independent sessions used by permissions.
    user_data = schemas.CreateUserSchema(
        name="Test User",
        email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        password="Pass1234",
        role=models.UserRole.USER,
    )
    user = user_repo.create_user(user_data)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_token(test_user) -> str:
    """
    Create a valid JWT token for the test user.

    Returns:
        str: A valid JWT token that can be used in Authorization header

    Example:
        def test_protected_endpoint(test_client, test_token):
            headers = {"Authorization": f"Bearer {test_token}"}
            response = test_client.get("/api/v1/users/me", headers=headers)
    """
    return create_test_token(
        user_id=str(test_user.id),
        role=models.UserRole.USER,
        name=test_user.name,
        email=test_user.email,
    )


@pytest.fixture(scope="function")
def test_admin_user(db: Session, user_repo: UserRepository):
    """
    Create a test admin user in the database for admin endpoint testing.

    Returns:
        models.User: An admin user instance persisted in the test database
    """
    user_data = schemas.CreateUserSchema(
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        password="Pass1234",
        role=models.UserRole.SUDO,
    )
    user = user_repo.create_user(user_data)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_admin_token(test_admin_user) -> str:
    """Create a valid JWT token for the test admin user."""
    return create_test_token(
        user_id=str(test_admin_user.id),
        role=models.UserRole.SUDO,
        name=test_admin_user.name,
        email=test_admin_user.email,
    )


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_client(db: Session):
    """
    Provide a FastAPI test client with database session override.

    This fixture overrides the database dependency to use the test
    database with automatic transaction rollback for isolation.

    Yields:
        TestClient: FastAPI test client configured for testing

    Example:
        def test_get_users(test_client):
            response = test_client.get("/api/v1/users/search")
            assert response.status_code == 200
    """

    # Override database dependency
    def override_get_sql_db():
        return db

    app.dependency_overrides[get_sql_db] = override_get_sql_db

    with TestClient(app) as client:
        yield client

    # Clear overrides after test
    app.dependency_overrides.clear()
