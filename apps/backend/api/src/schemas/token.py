"""Token schemas module.

This module contains Pydantic models for JWT token handling and authentication.
It defines the structure for token payloads and token responses used in the
authentication system.

The module includes:
- TokenPayload: JWT token payload structure
- Token: Authentication token response model
"""

from pydantic import BaseModel

from src.models.dtypes import UserRole


class TokenPayload(BaseModel):
    """JWT token payload model.

    Defines the structure of data contained within JWT tokens.
    This payload is encoded into the token and used for user
    identification and authorization.

    Attributes:
        username: User's unique identifier
        rol: User's role for permission validation
    """

    # === USER FIELDS ===
    id: str
    name: str
    email: str
    role: UserRole

    # === TOKEN INFORMATION ===
    sub: str
    iat: int
    exp: int
    jti: str
