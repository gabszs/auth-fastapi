from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi import Depends
from fastapi_cache.decorator import cache

from app.core.cache import cache_key_builder
from app.core.dependencies import ApiKeyDependency
from app.core.dependencies import CurrentUserDependency
from app.core.dependencies import FindBase
from app.core.dependencies import WebHookServiceDependency
from app.core.queue import queue
from app.schemas.webhook_schema import BaseWebHookSchema
from app.schemas.webhook_schema import WebHookListResultSchema
from app.schemas.webhook_schema import WebHookSchema
from app.schemas.webhook_schema import WebHookUpdateSchema

router = APIRouter(prefix="/webhooks", tags=["WebHook"])


# webhook_id=c56aa39a-1194-4c49-bec4-473b886b2c3d
# api_key=apk_test_01jy57b956xchdjj9dgnr0zfh5
# user_id=193d9dc1-e386-48e8-b0c6-bb669f0cc7ea
@router.post("/{webhook_id}", status_code=202)
async def trigger(
    webhook_id: UUID,
    service: WebHookServiceDependency,
    api_key: ApiKeyDependency,
):
    await service.trigger_webhook(webhook_id, api_key)


@router.get("-status/{task_id}")
async def get_webhook_status(task_id: str):
    result = AsyncResult(task_id, app=queue)
    return {"task_id": task_id, "state": result.state, "result": result.result}


@router.get("/", response_model=WebHookListResultSchema)
async def get_webhook_list(
    service: WebHookServiceDependency,
    current_user: CurrentUserDependency,
    find_query: FindBase = Depends(),
):
    return await service.get_list(find_query)


@router.get("/{id}", response_model=WebHookSchema)
@cache(key_builder=cache_key_builder("WebHookService", "id"))
async def get_by_id(
    id: UUID,
    service: WebHookServiceDependency,
    current_user: CurrentUserDependency,
):
    webhook = await service.get_by_id(id)
    return WebHookSchema.model_validate(webhook)


@router.post("/", status_code=201, response_model=WebHookSchema)
async def create_webhook(
    webhook: BaseWebHookSchema, service: WebHookServiceDependency, current_user: CurrentUserDependency
):
    return await service.add(user_id=current_user.id, schema=webhook)


@router.put("/{id}", response_model=WebHookSchema)
async def update_webhook(
    id: UUID,
    webhook: WebHookUpdateSchema,
    service: WebHookServiceDependency,
    current_user: CurrentUserDependency,
):
    return await service.patch(id=id, schema=webhook)


@router.delete("/{id}", status_code=204)
async def delete_webhook(
    id: UUID,
    service: WebHookServiceDependency,
    current_user: CurrentUserDependency,
):
    await service.remove_by_id(id)
