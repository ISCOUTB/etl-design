"""
Tests for UserService business logic.

These tests verify service-layer logic using mocked database
connections and repository methods to isolate business logic.
"""

from unittest.mock import Mock

import pytest

from src import models, schemas
from src.exceptions import UserNotFoundException
from src.services import UserService
from tests.utils.factories import UserFactory


class TestUserServiceGetOperations:
    """Test user retrieval service operations."""

    def test_get_user_by_id_success(self, user_service: UserService):
        """Test retrieving a user by ID when user exists."""
        user = UserFactory.create(id="user-123", name="Alice")

        # Mock the repository
        user_service.repository.get_user_by_id = Mock(return_value=user)

        result = user_service.get_user_by_id("user-123")

        # Verify repository was called correctly
        user_service.repository.get_user_by_id.assert_called_once_with("user-123")
        # Verify result contains expected data
        assert result.name == "Alice"

    def test_get_user_by_id_not_found(self, user_service: UserService):
        """Test that UserNotFoundException is raised when user not found."""
        user_service.repository.get_user_by_id = Mock(return_value=None)

        with pytest.raises(UserNotFoundException):
            user_service.get_user_by_id("nonexistent-id")

    def test_get_user_by_email_success(self, user_service: UserService):
        """Test retrieving a user by email when user exists."""
        user = UserFactory.create(email="alice@example.com", name="Alice")

        user_service.repository.get_by_email = Mock(return_value=user)

        result = user_service.get_user_by_email("alice@example.com")

        user_service.repository.get_by_email.assert_called_once_with(
            "alice@example.com"
        )
        assert result.name == "Alice"

    def test_get_user_by_email_not_found(self, user_service: UserService):
        """Test that UserNotFoundException is raised when email not found."""
        user_service.repository.get_by_email = Mock(return_value=None)

        with pytest.raises(UserNotFoundException):
            user_service.get_user_by_email("nonexistent@example.com")


class TestUserServiceSearchOperations:
    """Test user search service operations."""

    def test_search_users_with_no_filters(self, user_service: UserService):
        """Test searching all users without filters."""
        users = [
            UserFactory.create(id="user-1", name="Alice"),
            UserFactory.create(id="user-2", name="Bob"),
        ]

        user_service.repository.search_users = Mock(return_value=users)

        results = user_service.search_users()

        user_service.repository.search_users.assert_called_once()
        assert len(results) == 2

    def test_search_users_with_name_filter(self, user_service: UserService):
        """Test searching users by name."""
        users = [UserFactory.create(name="Alice")]

        user_service.repository.search_users = Mock(return_value=users)

        results = user_service.search_users(name="Alice")

        user_service.repository.search_users.assert_called_once_with(
            active_only=True,
            name="Alice",
            email=None,
            role=None,
            skip=None,
            limit=None,
        )
        assert len(results) == 1

    def test_search_users_with_role_filter(self, user_service: UserService):
        """Test searching users by role."""
        users = [
            UserFactory.create(id="user-1", name="Admin", role=models.UserRole.SUDO),
        ]

        user_service.repository.search_users = Mock(return_value=users)

        results = user_service.search_users(role=models.UserRole.SUDO)

        # Verify repository was called with correct parameters
        user_service.repository.search_users.assert_called_once()
        assert results[0].role == models.UserRole.SUDO

    def test_search_users_with_pagination(self, user_service: UserService):
        """Test searching users with pagination."""
        users = [UserFactory.create(id="user-1", name="Alice")]

        user_service.repository.search_users = Mock(return_value=users)

        results = user_service.search_users(skip=0, limit=10)

        user_service.repository.search_users.assert_called_once_with(
            active_only=True,
            name=None,
            email=None,
            role=None,
            skip=0,
            limit=10,
        )
        assert len(results) == 1

    def test_count_users(self, user_service: UserService):
        """Test counting users."""
        user_service.repository.count_users = Mock(return_value=42)

        count = user_service.count_users()

        assert count == 42
        user_service.repository.count_users.assert_called_once()


class TestUserServiceCreateOperations:
    """Test user creation service operations."""

    def test_create_user_success(self, user_service: UserService):
        """Test successfully creating a new user."""
        user_data = schemas.CreateUserSchema(
            name="Alice",
            email="alice@example.com",
            password="SecurePass123",
            role=models.UserRole.USER,
        )
        created_user = UserFactory.create(
            name="Alice", email="alice@example.com", id="new-user-id"
        )

        user_service.repository.create_user = Mock(return_value=created_user)
        user_service.repository.db.commit = Mock()

        result = user_service.create_user(user_data)

        user_service.repository.create_user.assert_called_once_with(user_data)
        user_service.repository.db.commit.assert_called_once()
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    def test_create_user_with_email_in_use_error(self, user_service: UserService):
        """Test that EmailInUseException is raised for duplicate email."""
        from sqlalchemy.exc import IntegrityError

        user_data = schemas.CreateUserSchema(
            name="Alice",
            email="alice@example.com",
            password="SecurePass123",
            role=models.UserRole.USER,
        )
        created_user = UserFactory.create(name="Alice", email="alice@example.com")

        user_service.repository.create_user = Mock(return_value=created_user)

        # Mock IntegrityError
        error = IntegrityError("statement", "params", Exception("uq_user_email"))
        user_service.repository.db.commit = Mock(side_effect=error)
        user_service.repository.db.rollback = Mock()

        from src.exceptions import EmailInUseException

        with pytest.raises(EmailInUseException):
            user_service.create_user(user_data)

        user_service.repository.db.rollback.assert_called_once()


class TestUserServiceUpdateOperations:
    """Test user update service operations."""

    def test_update_user_success(self, user_service: UserService):
        """Test successfully updating a user."""
        user_id = "user-123"
        update_data = schemas.UpdateUserSchema(name="Alice Smith")
        updated_user = UserFactory.create(id=user_id, name="Alice Smith")

        user_service.repository.update_user = Mock(return_value=updated_user)
        user_service.repository.db.commit = Mock()

        result = user_service.update_user(user_id, update_data)

        user_service.repository.update_user.assert_called_once()
        user_service.repository.db.commit.assert_called_once()
        assert result.name == "Alice Smith"


class TestUserServiceDeleteOperations:
    """Test user deletion service operations."""

    def test_delete_user_success(self, user_service: UserService):
        """Test successfully deleting a user."""
        user_id = "user-123"
        deleted_user = UserFactory.create(id=user_id)

        user_service.repository.get_user_by_id = Mock(return_value=deleted_user)
        user_service.repository.inactivate_user = Mock(return_value=deleted_user)
        user_service.repository.db.commit = Mock()

        result = user_service.delete_user(user_id)

        user_service.repository.get_user_by_id.assert_called_once()
        user_service.repository.db.commit.assert_called_once()
        # Result should be the response schema of the user
        assert result.name == "Test User"
