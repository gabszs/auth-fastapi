import ulid

from app.core.telemetry import instrument
from app.repository import ApiKeyRepository
from app.schemas.api_key_schema import BaseApiKeySchema
from app.schemas.api_key_schema import CompleteApiKeySchema
from app.services.base_service import BaseService


@instrument
class ApiKeyService(BaseService):
    def __init__(self, api_token_repository: ApiKeyRepository) -> None:
        super().__init__(api_token_repository)

    async def add(self, username: str, schema: BaseApiKeySchema, **kwargs):  # type: ignore
        input_schema = CompleteApiKeySchema(
            **schema.model_dump(), token=f"apk_{username}_{ulid.new().str.lower()}", is_active=True
        )
        return await self._repository.create(input_schema, **kwargs)
