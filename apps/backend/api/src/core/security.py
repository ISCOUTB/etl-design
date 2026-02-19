import hashlib
import hmac

import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plain text password matches its hash.

    Args:
        plain_password (str): Plain text password to verify.
        hashed_password (str): Encrypted password (hash) to compare against.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    """
    Generates an encrypted hash of a plain text password.

    Args:
        password (str): Plain text password to encrypt.

    Returns:
        str: Encrypted hash of the password.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt=salt)
    return hashed.decode()


def derive_key(
    secret: str,
    info: str,
    length: int = 32,
) -> bytes:
    salt = b""
    prk = hmac.new(
        salt if salt else (b"\x00" * hashlib.sha256().digest_size),
        secret.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    info_bytes = info.encode("utf-8")

    okm = b""
    previous = b""

    for i in range(
        (length + hashlib.sha256().digest_size - 1) // hashlib.sha256().digest_size
    ):
        previous = hmac.new(
            prk, previous + info_bytes + bytes([i + 1]), hashlib.sha256
        ).digest()
        okm += previous

    return okm[:length]
