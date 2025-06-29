from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi_cache.decorator import cache

from app.core.cache import cache_key_builder
from app.core.dependencies import ApiKeyServiceDependency
from app.core.dependencies import CurrentUserDependency
from app.core.dependencies import FindBase
from app.schemas.api_key_schema import ApiKeyListResultSchema
from app.schemas.api_key_schema import ApiKeySchema
from app.schemas.api_key_schema import ApiKeyUpdateSchema
from app.schemas.api_key_schema import BaseApiKeySchema

router = APIRouter(prefix="/api-key", tags=["ApiKey"])


@router.get("/", response_model=ApiKeyListResultSchema)
async def get_api_key_list(
    service: ApiKeyServiceDependency,
    current_user: CurrentUserDependency,
    find_query: FindBase = Depends(),
):
    return await service.get_list(find_query)


@router.get("/{id}", response_model=ApiKeySchema)
@cache(key_builder=cache_key_builder("ApiKeyService", "id"))
async def get_by_id(
    id: UUID,
    service: ApiKeyServiceDependency,
    current_user: CurrentUserDependency,
):
    api_key = await service.get_by_id(id)
    return ApiKeySchema.model_validate(api_key)


@router.post("/", status_code=201, response_model=ApiKeySchema)
async def create_api_key(
    api_key: BaseApiKeySchema, service: ApiKeyServiceDependency, current_user: CurrentUserDependency
):
    return await service.add(username=current_user.username, schema=api_key)


@router.put("/{id}", response_model=ApiKeySchema)
async def update_api_key(
    id: UUID,
    api_key: ApiKeyUpdateSchema,
    service: ApiKeyServiceDependency,
    current_user: CurrentUserDependency,
):
    return await service.patch(id=id, schema=api_key)


@router.delete("/{id}", status_code=204)
async def delete_api_key(
    id: UUID,
    service: ApiKeyServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.remove_by_id(id)
