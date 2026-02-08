from datetime import timedelta
from typing import List

from app.core.cache import CacheManager
from app.core.exceptions import exceptions
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.settings import settings
from app.core.telemetry import instrument
from app.models import User
from app.repository.user_repository import UserRepository
from app.schemas.auth_schema import Payload, SignIn, SignInResponse, SignUp
from app.schemas.user_schema import BaseUserWithPassword
from app.services.base_service import BaseService


@instrument(pyroscope_tagging=True)
class AuthService(BaseService):
    def __init__(self, user_repository: UserRepository, cache: CacheManager) -> None:
        self.user_repository = user_repository
        super().__init__(user_repository, cache)

    async def sign_in(self, sign_in_info: SignIn):
        user: List[User] = await self.user_repository.read_by_email(email=sign_in_info.email, unique=True)
        if not user:
            raise exceptions.invalid_credentials(detail="Incorrect email or user not exist")
        found_user = user[0]

        if not verify_password(sign_in_info.password, found_user.password):
            raise exceptions.invalid_credentials(detail="Incorrect password")

        delattr(found_user, "password")

        payload = Payload(
            id=str(found_user.id),
            email=found_user.email,
            username=found_user.username,
        )
        token_lifespan = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expiration_datetime = create_access_token(payload.model_dump(), token_lifespan)
        sign_in_result = SignInResponse(
            access_token=access_token,
            expiration=expiration_datetime,
            user_info=found_user,
        )
        return sign_in_result

    async def sign_up(self, user_info: SignUp) -> User:
        user = BaseUserWithPassword(**user_info.model_dump(exclude_none=True))
        user.password = get_password_hash(user_info.password)
        created_user = await self.user_repository.create(user)
        delattr(created_user, "password")
        return created_user

    async def refresh_token(self, current_user: User):
        payload = Payload(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
        )
        token_lifespan = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expiration_datetime = create_access_token(payload.model_dump(), token_lifespan)
        sign_in_result = SignInResponse(
            access_token=access_token,
            expiration=expiration_datetime,
            user_info=current_user,
        )
        return sign_in_result


#  payload = Payload(id=str(found_user.id), email=found_user.email, username=found_user.username)
#         token_lifespan = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token, expiration_datetime = create_access_token(payload.model_dump(), token_lifespan)
#         sign_in_result = SignInResponse(access_token=access_token, expiration=expiration_datetime, user_info=found_user)
#         return sign_in_result
