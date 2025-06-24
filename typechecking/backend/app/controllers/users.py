from typing import Literal

import app.models as models
import app.schemas as schemas
from app.controllers.utils import valid_email, valid_phone
from app.core.security import verify_password, get_password_hash

from sqlalchemy import select, Select
from sqlalchemy.orm import Session


class ControllerUsers:
    @staticmethod
    def get_user_rol(
        search_user: schemas.users.SearchUser, db: Session, active: bool = True
    ) -> models.user_roles.UserRoles | None:
        """
        Gets a user instance directly from the user roles table.

        Args:
            search_user (schemas.users.SearchUser): User search information to find in the database.
            db (Session): Database session for making queries to the sql database.
            active (bool): Limitation to only get an active user. Default is True.

        Returns:
            models.user_roles.UserRoles | None: Returns a UserRoles object if it exists, otherwise returns None.
        """
        conditions = [
            models.user_roles.UserRoles.username == search_user.username,
            models.user_roles.UserRoles.rol == search_user.rol,
        ]
        if active:
            conditions.append(models.user_roles.UserRoles.is_active)

        return db.query(models.user_roles.UserRoles).filter(*conditions).first()

    @staticmethod
    def get_user_by_username(
        username: str, db: Session, active: bool = True
    ) -> models.user_roles.UserRoles | None:
        """
        Gets a user by username from the user roles table.

        Args:
            username (str): Username of the user to find.
            db (Session): Database session for making queries to the sql database.
            active (bool): Limitation to only get an active user. Default is True.

        Returns:
            models.user_roles.UserRoles | None: Returns a UserRoles object if it exists, otherwise returns None.
        """
        conditions = [models.user_roles.UserRoles.username == username]
        if active:
            conditions.append(models.user_roles.UserRoles.is_active)

        return db.query(models.user_roles.UserRoles).filter(*conditions).first()

    @classmethod
    def authenticate_user(
        cls, user_login: schemas.users.LoginUser, db: Session
    ) -> models.user_roles.UserRoles | None:
        """
        Authenticates that the user exists in the database when logging in.

        Args:
            user_login (schemas.users.LoginUser): User login information to enter the system.
            db (Session): Database session for making queries to the sql database.

        Returns:
            models.user_roles.UserRoles | None: Returns a UserRoles object if the user was authenticated
            correctly. Otherwise returns None.
        """
        user_search = schemas.users.SearchUser(
            username=user_login.username, rol=user_login.rol
        )
        user: models.user_roles.UserRoles | None = cls.get_user_rol(user_search, db)

        if user is None:
            return None
        if not verify_password(user_login.password, user.password):
            return None

        return user

    @staticmethod
    def join_users(active: bool = True) -> Select:
        """
        Creates a SQL statement to join user information and user roles tables.

        Args:
            active (bool): Filter to only include active users. Default is True.

        Returns:
            Select: SQL select statement joining UserInfo and UserRoles tables.
        """
        stmt = select(
            models.user_info.UserInfo.username,
            models.user_info.UserInfo.name,
            models.user_info.UserInfo.surname,
            models.user_info.UserInfo.sex,
            models.user_info.UserInfo.phone,
            models.user_info.UserInfo.email,
            models.user_roles.UserRoles.rol,
            models.user_roles.UserRoles.is_active,
        ).join(
            models.user_roles.UserRoles,
            models.user_info.UserInfo.username == models.user_roles.UserRoles.username,
        )

        if active:
            stmt = stmt.where(models.user_roles.UserRoles.is_active)

        print(stmt, type(stmt))
        return stmt

    @classmethod
    def get_user(
        cls,
        username: str,
        db: Session,
        active: bool = True,
        rol: bool = False,
    ) -> schemas.users.AllUser | schemas.users.BaseUser | None:
        """
        Gets basic information of a system user regardless of role.

        Args:
            username (str): Username of the user to find.
            db (Session): Database session for making queries to the sql database.
            active (bool): Filter to ensure the user has at least one active role in the hospital. Default is True.
            rol (bool): Specifies if all roles of the same user should be shown.
                When rol=True, the function returns an AllUser object and BaseUser when rol=False.
                Default is False.

        Returns:
            schemas.users.AllUser | schemas.users.BaseUser | None: When rol=False the function returns BaseUser,
            when rol=True, it returns AllUser. If the user is not found, returns None.
        """
        stmt = cls.join_users(active).where(
            models.user_info.UserInfo.username == username
        )
        query = db.execute(stmt).all()
        if not query:
            return None

        userbase = schemas.users.BaseUser(
            username=query[0][0],
            name=query[0][1],
            surname=query[0][2],
            sex=query[0][3],
            phone=query[0][4],
            email=query[0][5],
        )
        if rol:
            roles: list[schemas.users.RolesInfo] = list(
                map(lambda row: {"rol": row[-2], "is_active": row[-1]}, query)
            )
            return schemas.users.AllUser(**userbase.model_dump(), roles=roles)

        return userbase

    @classmethod
    def create_user(
        cls, new_user: schemas.users.CreateUser, db: Session, admin: bool = True
    ) -> Literal[0, 1, 2, 3, 4]:
        """
        Creates a new user in the system. This operation is exclusively reserved for system administrators,
        and, if wanting to add an administrator, only the superuser could perform it.

        For users that are not previously added to the system, their space will be created without problems.
        If the user with that role exists in the system as inactive, it will only change state, otherwise,
        the operation cannot be performed.

        Args:
            new_user (schemas.users.CreateUser): Information of the new user.
            db (Session): Database session for making queries to the sql database.
            admin (bool): Validates if you want to add administrator information. Default is True.

        Returns:
            Literal[0, 1, 2, 3, 4]: Returns an integer symbolizing the response status. These are the possible response states:
                - 0: Successful response
                - 1: User is administrator, cannot be edited. Only appears when admin=False.
                - 2: Active user with same username
                - 3: User with same email
                - 4: User with same phone number
        """
        if new_user.rol == "admin" and not admin:
            return 1

        user: schemas.users.AllUser = cls.get_user(
            new_user.username, db, rol=True, active=False
        )

        # Create user information if not exists in the system
        if user is None:
            user_info = models.user_info.UserInfo(
                username=new_user.username,
                name=new_user.name,
                surname=new_user.surname,
                sex=new_user.sex,
                phone=new_user.phone,
                email=new_user.email,
            )

            if new_user.email is not None and not valid_email(new_user.email, db):
                return 3

            if new_user.phone is not None and not valid_phone(new_user.phone, db):
                return 4

            db.add(user_info)

        user_rol: models.user_roles.UserRoles | None = cls.get_user_rol(
            schemas.users.SearchUser(username=new_user.username, rol=new_user.rol),
            db,
            False,
        )

        # Create user role if not exists
        if user_rol is None:
            new_user_rol = models.user_roles.UserRoles(
                username=new_user.username,
                rol=new_user.rol,
                password=get_password_hash(new_user.password),
                is_active=True,
            )
            db.add(new_user_rol)
            db.commit()

            return 0

        # If user role is active, return status
        if user_rol.is_active:
            return 2

        user_rol.is_active = True
        db.commit()
        db.refresh(user_rol)
        return 0
