from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi_cache.decorator import cache

from app.core.cache import cache_key_builder
from app.core.dependencies import CurrentUserDependency
from app.core.dependencies import FindBase
from app.core.dependencies import UserServiceDependency
from app.core.telemetry import logger
from app.core.security import authorize
from app.models.models_enums import UserRoles
from app.schemas.base_schema import Message
from app.schemas.user_schema import BaseUserWithPassword
from app.schemas.user_schema import FindUserResult
from app.schemas.user_schema import UpsertUser
from app.schemas.user_schema import User

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/", response_model=FindUserResult)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN, UserRoles.BASE_USER])
async def get_user_list(
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
    find_query: FindBase = Depends(),
):
    logger.info("GET /user/ - user_id=%s", current_user.id)
    return await service.get_list(find_query)


@router.get("/{id}", response_model=User)
@cache(key_builder=cache_key_builder("UserService", "id"))
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def get_by_id(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    logger.info("GET /user/%s - user_id=%s", id, current_user.id)
    return await service.get_by_id(id)


@router.post("/", status_code=201, response_model=User)
async def create_user(user: BaseUserWithPassword, service: UserServiceDependency):
    logger.info("POST /user/ - email=%s", user.email)
    return await service.add(user)


### importante tem de fazer
### adicionar validacao para quano o a request tiver parametros iguais ao do current_user
@router.put("/{id}", response_model=User)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def update_user(
    id: UUID,
    user: UpsertUser,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    logger.info("PUT /user/%s - user_id=%s", id, current_user.id)
    return await service.patch(id=id, schema=user)


@router.patch("/enable_user/{id}", response_model=Message)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def enabled_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    logger.info("PATCH /user/enable_user/%s - user_id=%s", id, current_user.id)
    await service.patch_attr(id=id, attr="is_active", value=True)
    return Message(detail="User has been enabled successfully")


@router.patch("/disable/{id}", response_model=Message)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def disable_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    logger.info("PATCH /user/disable/%s - user_id=%s", id, current_user.id)
    await service.patch_attr(id=id, attr="is_active", value=False)
    return Message(detail="User has been desabled successfully")


@router.delete("/{id}", status_code=204)
@authorize(role=[UserRoles.ADMIN])
async def delete_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    logger.info("DELETE /user/%s - user_id=%s", id, current_user.id)
    await service.remove_by_id(id)
