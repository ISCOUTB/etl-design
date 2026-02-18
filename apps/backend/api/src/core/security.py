from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plain text password matches its hash.

    Args:
        plain_password (str): Plain text password to verify.
        hashed_password (str): Encrypted password (hash) to compare against.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates an encrypted hash of a plain text password.

    Args:
        password (str): Plain text password to encrypt.

    Returns:
        str: Encrypted hash of the password.
    """
    return pwd_context.hash(password)
