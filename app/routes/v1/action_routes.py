from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi_cache.decorator import cache

from app.core.cache import cache_key_builder
from app.core.dependencies import ActionServiceDependency
from app.core.dependencies import CurrentUserDependency
from app.core.dependencies import FindBase
from app.core.security import authorize
from app.models.models_enums import UserRoles
from app.schemas.action_schema import ActionListResultSchema
from app.schemas.action_schema import ActionSchema
from app.schemas.action_schema import ActionUpdateSchema
from app.schemas.action_schema import BaseActionSchema

router = APIRouter(prefix="/action", tags=["Action"])


@router.get("/", response_model=ActionListResultSchema)
async def get_action_list(
    service: ActionServiceDependency,
    current_user: CurrentUserDependency,
    find_query: FindBase = Depends(),
):
    return await service.get_list(find_query)


@router.get("/{id}", response_model=ActionSchema)
@cache(key_builder=cache_key_builder("ActionService", "id"))
async def get_by_id(
    id: UUID,
    service: ActionServiceDependency,
    current_user: CurrentUserDependency,
):
    action = await service.get_by_id(id)
    return ActionSchema.model_validate(action)


@router.post("/", status_code=201, response_model=ActionSchema)
async def create_action(
    action: BaseActionSchema, service: ActionServiceDependency, current_user: CurrentUserDependency
):
    return await service.add(user_id=current_user.id, schema=action)


@router.post("/{id}/upload", response_model=ActionSchema)
async def upload_file_to_action(
    id: UUID,
    file: UploadFile,
    service: ActionServiceDependency,
    current_user: CurrentUserDependency,
):
    return await service.upload_file(id=id, file=file)


@router.put("/{id}", response_model=ActionSchema)
async def update_action(
    id: UUID,
    action: ActionUpdateSchema,
    service: ActionServiceDependency,
    current_user: CurrentUserDependency,
):
    return await service.patch(id=id, schema=action)


@router.delete("/{id}", status_code=204)
@authorize(role=[UserRoles.ADMIN], allow_same_id=True)
async def delete_action(
    id: UUID,
    service: ActionServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.remove_by_id(id)
