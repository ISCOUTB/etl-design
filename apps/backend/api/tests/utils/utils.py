"""
Test utilities and helper functions.

This module contains shared utilities used across test modules,
such as assertion helpers, data comparison functions, and common
test setup/teardown operations.
"""

from typing import Any


def assert_model_fields(obj: Any, **expected_fields) -> None:
    """
    Assert that an object has specific field values.

    Args:
        obj: The object to check
        **expected_fields: Field name and expected value pairs

    Example:
        user = UserFactory.create(name="Alice", email="alice@example.com")
        assert_model_fields(user, name="Alice", email="alice@example.com")
    """
    for field_name, expected_value in expected_fields.items():
        actual_value = getattr(obj, field_name)
        assert actual_value == expected_value, (
            f"Field {field_name}: expected {expected_value!r} but got {actual_value!r}"
        )


def assert_raises_validation_error(
    validation_func, expected_message: str | None = None
) -> None:
    """
    Assert that a Pydantic validation function raises a validation error.

    Args:
        validation_func: Callable that should raise a validation error
        expected_message: Optional substring that should appear in error message

    Example:
        def test_email_validation():
            assert_raises_validation_error(
                lambda: UserSchema(email="invalid-email"),
                expected_message="Invalid email format"
            )
    """
    from pydantic import ValidationError

    try:
        validation_func()
        assert False, "Expected ValidationError but no exception was raised"
    except ValidationError as e:
        if expected_message and expected_message not in str(e):
            assert False, f"Expected message '{expected_message}' not in error: {e}"
