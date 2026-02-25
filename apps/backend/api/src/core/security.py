import hashlib
import hmac

import bcrypt
from pyaegis import Aegis256


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


def encrypt_aegis256(
    plaintext: str,
    secret_key: str,
    secret_sign: str,
    *,
    project_id: str,
    field_name: str,
) -> str:
    nbytes = 32

    cipher = Aegis256(nbytes)
    key = derive_key(secret_key, secret_sign, nbytes)
    nonce = cipher.random_nonce()

    ciphertext = cipher.encrypt(
        key=key,
        nonce=nonce,
        plaintext=plaintext.encode("utf-8"),
        associated_data=f"{project_id}:{field_name}".encode("utf-8"),
    )
    return (nonce + ciphertext).hex()


def decrypt_aegis256(
    ciphertext_hex: str,
    secret_key: str,
    secret_sign: str,
    *,
    project_id: str,
    field_name: str,
) -> str:
    nbytes = 32

    cipher = Aegis256(nbytes)
    key = derive_key(secret_key, secret_sign, nbytes)

    ciphertext_bytes = bytes.fromhex(ciphertext_hex)
    nonce = ciphertext_bytes[:nbytes]
    ciphertext = ciphertext_bytes[nbytes:]

    plaintext_bytes = cipher.decrypt(
        key=key,
        nonce=nonce,
        ciphertext=ciphertext,
        associated_data=f"{project_id}:{field_name}".encode("utf-8"),
    )
    return plaintext_bytes.decode("utf-8")
