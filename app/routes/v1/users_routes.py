from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi_cache.decorator import cache

from app.core.cache import cache_key_builder
from app.core.dependencies import CurrentUserDependency
from app.core.dependencies import FindBase
from app.core.dependencies import UserServiceDependency
from app.core.security import authorize
from app.models.models_enums import UserRoles
from app.schemas.user_schema import BaseUserWithPasswordSchema
from app.schemas.user_schema import UserListResultSchema
from app.schemas.user_schema import UserSchema
from app.schemas.user_schema import UserUpdateSchema

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/", response_model=UserListResultSchema)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN, UserRoles.BASE_USER])
async def get_user_list(
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
    find_query: FindBase = Depends(),
):
    return await service.get_list(find_query)


@router.get("/{id}", response_model=UserSchema)
@cache(key_builder=cache_key_builder("UserService", "id"))
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def get_by_id(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    user = await service.get_by_id(id)
    return UserSchema.model_validate(user)


@router.post("/", status_code=201, response_model=UserSchema)
async def create_user(user: BaseUserWithPasswordSchema, service: UserServiceDependency):
    return await service.add(user)


### importante tem de fazer
### adicionar validacao para quano o a request tiver parametros iguais ao do current_user
@router.put("/{id}", response_model=UserSchema)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def update_user(
    id: UUID,
    user: UserUpdateSchema,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    return await service.patch(id=id, schema=user)


@router.patch("/enable_user/{id}", status_code=204)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def enabled_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.patch_attr(id=id, attr="is_active", value=True)


@router.patch("/disable/{id}", status_code=204)
@authorize(role=[UserRoles.MODERATOR, UserRoles.ADMIN], allow_same_id=True)
async def disable_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.patch_attr(id=id, attr="is_active", value=False)


@router.delete("/{id}", status_code=204)
@authorize(role=[UserRoles.ADMIN])
async def delete_user(
    id: UUID,
    service: UserServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.remove_by_id(id)
