"""
Tests for User SQLAlchemy model definition.

These tests verify model field definitions, constraints,
and relationships are properly configured.
"""

from src import models


class TestUserModelFields:
    """Test User model field definitions."""

    def test_user_has_required_fields(self):
        """Test that User model has all required fields."""
        required_fields = ["id", "name", "email", "role", "status", "password"]

        for field in required_fields:
            assert hasattr(models.User, field), f"User model missing {field} field"

    def test_user_default_role(self):
        """Test that user role defaults to USER."""
        assert models.User.role.default.arg == models.UserRole.USER

    def test_user_default_status(self):
        """Test that user status defaults to ACTIVE."""
        assert models.User.status.default.arg == models.Status.ACTIVE

    def test_user_has_relationships(self):
        """Test that User model has relationships."""
        assert hasattr(models.User, "projects")
        assert hasattr(models.User, "upload_tasks")

    def test_user_table_name(self):
        """Test that User model uses correct table name."""
        assert models.User.__tablename__ == "user"


class TestUserModelConstraints:
    """Test User model constraints and validations."""

    def test_user_email_unique_constraint_exists(self):
        """Test that unique constraint on email exists."""
        table = models.User.__table__
        constraints = [c for c in table.constraints if hasattr(c, "name")]
        constraint_names = [c.name for c in constraints]

        assert "uq_user_email" in constraint_names

    def test_user_email_format_check_constraint_exists(self):
        """Test that email format check constraint exists."""
        table = models.User.__table__
        constraints = [c for c in table.constraints if hasattr(c, "name")]
        constraint_names = [c.name for c in constraints]

        assert "ck_user_email_format" in constraint_names


class TestUserModelIndexes:
    """Test User model indexes."""

    def test_user_has_indexes(self):
        """Test that User model has defined indexes."""
        table = models.User.__table__
        index_names = [idx.name for idx in table.indexes]

        # Check that common indexes exist
        assert any("name" in name for name in index_names)
        assert any("email" in name for name in index_names)
        assert any("role" in name for name in index_names)
        assert any("status" in name for name in index_names)
