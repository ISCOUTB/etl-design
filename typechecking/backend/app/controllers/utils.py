import app.models as models

import re
from sqlalchemy import select
from sqlalchemy.orm import Session


def valid_email(email: str, db: Session) -> bool:
    """
    Valida si el email es válido de utilizar en el sistema, incluyendo la existencia de un usuario con el mismo email

    Args:
        email (str): Correo electrónico del usuario a validar.
        db (sqlalchemy.orm.Session): Sesión de la base de datos para hacer las consultas a la base de datos en Postgresql.

    Returns:
        bool: Retorna `True` si el email es válido, en caso contrario retorna `False`.
    """
    # Valida que el email este bien escrito
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return False

    # Validar que el email no esté repetido
    stmt = select(models.user_info.UserInfo.email).where(models.user_info.UserInfo.email == email)
    query = db.execute(stmt).all()
    if query:
        return False

    return True


def valid_phone(phone: str, db: Session) -> bool:
    """
    Valida si el teléfono es válido de utilizar en el sistema, incluyendo la existencia de un usuario con el mismo teléfono

    Args:
        phone (str): Teléfono del usuario a validar.
        db (sqlalchemy.orm.Session): Sesión de la base de datos para hacer las consultas a la base de datos en Postgresql.

    Returns:
        bool: Retorna `True` si el teléfono es válido, en caso contrario retorna `False`.
    """
    # Valida que el teléfono este bien escrito
    if not re.match(r"^\+?[1-9]\d{1,14}$", phone):
        return False

    # Validar que el teléfono no esté repetido
    stmt = select(models.user_info.UserInfo.phone).where(models.user_info.UserInfo.phone == phone)
    query = db.execute(stmt).all()
    if query:
        return False

    return True
