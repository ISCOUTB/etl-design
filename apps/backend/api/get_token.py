"""
Util python file just to get the token from the command line and print it to the console.
This is useful for testing the authentication and authorization of the API.
"""

import argparse
from datetime import timedelta

from src import schemas
from src.core.database_sql import SessionLocal
from src.services import AuthService, UserService
from src.utils import utc_now


def parse_args():
    parser = argparse.ArgumentParser(
        description="Get an authentication token for a user."
    )
    parser.add_argument("email", type=str, help="The email of the user.")
    parser.add_argument(
        "--timedelta-hours",
        "-t",
        type=int,
        default=1,
        help="The number of hours the token is valid for.",
    )
    return parser.parse_args()


def get_token(email: str, timedelta_hours: int = 1) -> str:
    with SessionLocal() as db:
        auth_service = AuthService(db=db)
        user_service = UserService(db=db)
        user = user_service.get_user_by_email(email=email)

        token_payload = schemas.TokenPayload(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            sub=str(user.id),
            iat=int(utc_now().timestamp()),
            exp=int((utc_now() + timedelta(hours=timedelta_hours)).timestamp()),
            jti=str(user.id) + "-" + str(int(utc_now().timestamp())),
        )

        token = auth_service.encode_access_token(token_payload)

    return token


def main() -> None:
    args = parse_args()
    token = get_token(
        email=args.email,
        timedelta_hours=args.timedelta_hours,
    )
    print(token)


if __name__ == "__main__":
    main()
