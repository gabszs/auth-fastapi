from datetime import datetime
from datetime import timedelta
from functools import wraps
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import bcrypt
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt

from app.core.exceptions import http_errors
from app.core.settings import settings
from app.models.models_enums import UserRoles

secret_key = settings.SECRET_KEY
algorithm = settings.ALGORITHM


def authorize(role: List[UserRoles], allow_same_id: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_role = kwargs.get("current_user").role
            have_authorization = user_role in role
            if allow_same_id:
                is_same_id = kwargs.get("current_user").id == kwargs.get("id")
                if not is_same_id and not have_authorization:
                    raise http_errors.auth_error("Not enough permissions")
                return await func(*args, **kwargs)
            if not have_authorization:
                raise http_errors.auth_error("Not enough permissions")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def create_access_token(subject: Dict[str, str], expires_delta: timedelta = timedelta(minutes=30)) -> Tuple[str, str]:
    expire = (
        datetime.now() + expires_delta
        if expires_delta
        else datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload = {"exp": int(round(expire.timestamp())), **subject}
    encoded_jwt = jwt.encode(payload, secret_key, algorithm)
    expiration_datetime = expire.strftime(settings.DATETIME_FORMAT)
    return encoded_jwt, expiration_datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_enc = plain_password.encode("utf-8")
    hashed_byte_password = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_byte_password)


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def decote_jwt(token: str) -> Optional[str]:
    try:
        decoded_token = jwt.decode(
            token,
            secret_key,
            algorithms=algorithm,
            options={"verify_exp": False},
        )
        return decoded_token if decoded_token["exp"] >= int(round(datetime.now().timestamp())) else None
    except Exception as _:
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = False):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise http_errors.auth_error(detail="Authentication failed: invalid scheme, expected 'Bearer'")
            if not self.verify_jwt(credentials.credentials):
                raise http_errors.auth_error(detail="Authentication failed: token is invalid or expired")
            return credentials.credentials
        else:
            raise http_errors.auth_error(detail="Authentication failed: no authorization token provided")

    def verify_jwt(self, jwt_token: str) -> bool:
        is_token_valid: bool = False

        try:
            payload = decote_jwt(jwt_token)
        except Exception as _:
            payload = None
        if payload:
            is_token_valid = True
        return is_token_valid
