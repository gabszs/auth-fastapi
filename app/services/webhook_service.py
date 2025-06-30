from typing import Any
from uuid import UUID

from app.core.exceptions import AuthError
from app.core.exceptions import NotFoundError
from app.core.telemetry import instrument
from app.core.telemetry import logger
from app.repository import ActionRepository
from app.repository import WebHookRepository
from app.schemas.webhook_schema import BaseWebHookSchema
from app.schemas.webhook_schema import CompleteWebHookSchema
from app.services.base_service import BaseService
from worker.main import create_items


@instrument
class WebHookService(BaseService):
    def __init__(self, webhook_repository: WebHookRepository, action_repository: ActionRepository) -> None:
        self._action_repository = action_repository
        super().__init__(webhook_repository)

    async def add(self, user_id: UUID, schema: BaseWebHookSchema, **kwargs):  # type: ignore
        # user id: 193d9dc1-e386-48e8-b0c6-bb669f0cc7ea
        action = await self._action_repository.read_by_id(schema.action_id)
        if action.user_id != user_id:
            raise NotFoundError(detail=f"Resource with id={action.user_id} not found")
        input_schema = CompleteWebHookSchema(**schema.model_dump(), is_active=True)

        webhook = await self._repository.create(input_schema, **kwargs)
        logger.info(f"Webhook sucessifuly created with id: {webhook.id}")
        return webhook

    async def trigger_webhook(self, id: UUID, api_key: Any):
        webhook = await self._repository.read_by_id(id, eager=True)  # se nao existir, ele ja dispara o erro
        if webhook.action.user_id != api_key.user.id:
            raise AuthError(detail="You do not have permission to access this webhook.")

        # action = await self._action_repository.read_by_id(schema.action_id)

        input_data = {
            "BEES_ENTITY_ITEMS": webhook.action.url,
            "BEES_VERSION_API_V2": webhook.action.path_url,
            "BEES_URL_V1": webhook.action.body_version,
            "MAPPING": webhook.action.file_mapping,
        }
        logger.info(f"Webhook with id: {webhook.id} succesifully triggered", extra=input_data)
        create_items.delay(input_data)
