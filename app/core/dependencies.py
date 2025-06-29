from typing import Annotated

from fastapi import Depends
from fastapi import Header
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.database import sessionmanager
from app.core.exceptions import AuthError
from app.core.exceptions import InvalidCredentials
from app.core.security import JWTBearer
from app.core.settings import settings
from app.models import ApiKey
from app.models import User
from app.repository import ActionRepository
from app.repository import ApiKeyRepository
from app.repository import UserRepository
from app.repository import WebHookRepository
from app.schemas.auth_schema import Payload
from app.schemas.base_schema import FindBase
from app.services import ActionService
from app.services import ApiKeyService
from app.services import AuthService
from app.services import UserService
from app.services import WebHookService


async def get_user_service(session: Session = Depends(sessionmanager.session)) -> UserService:
    user_repository = UserRepository(session=session)
    return UserService(user_repository)


async def get_current_user(token: str = Depends(JWTBearer()), service: UserService = Depends(get_user_service)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        token_data = Payload(**payload)
    except (jwt.JWTError, ValidationError):
        raise AuthError(detail="Could not validate credentials")
    current_user: User = await service.get_by_id(token_data.id)  # type: ignore
    if not current_user:
        raise AuthError(detail="User not found")
    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise AuthError("Inactive user")
    return current_user


async def get_auth_service(session: Session = Depends(sessionmanager.session)):
    user_repository = UserRepository(session=session)
    return AuthService(user_repository=user_repository)


async def get_action_service(session: Session = Depends(sessionmanager.session)) -> ActionService:
    action_repository = ActionRepository(session=session)
    return ActionService(action_repository)


async def get_api_key_service(session: Session = Depends(sessionmanager.session)) -> ApiKeyService:
    api_key_repository = ApiKeyRepository(session=session)
    return ApiKeyService(api_key_repository)


async def get_webhook_service(session: Session = Depends(sessionmanager.session)) -> WebHookService:
    webhook_repository = WebHookRepository(session=session)
    action_repository = ActionRepository(session=session)
    return WebHookService(webhook_repository, action_repository)


async def get_current_api_key(
    x_api_key: str = Header(..., alias="x-api-key"), service: ApiKeyService = Depends(get_api_key_service)
) -> ApiKey:
    if not x_api_key:
        raise AuthError(detail="API key is required.")

    api_key = await service.get_by_param("token", x_api_key, eager=True)
    if not api_key or not api_key.is_active:
        raise InvalidCredentials(detail="Invalid or inactive API key.")

    return api_key


FindQueryParameters = Annotated[FindBase, Depends()]
SessionDependency = Annotated[Session, Depends(get_db)]
UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
CurrentUserDependency = Annotated[User, Depends(get_current_user)]
AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
CurrentActiveUserDependency = Annotated[User, Depends(get_current_active_user)]
ApiKeyDependency = Annotated[ApiKey, Depends(get_current_api_key)]

ActionServiceDependency = Annotated[ActionService, Depends(get_action_service)]
ApiKeyServiceDependency = Annotated[ApiKeyService, Depends(get_api_key_service)]
WebHookServiceDependency = Annotated[ApiKeyService, Depends(get_webhook_service)]
