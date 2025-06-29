import base64
from uuid import UUID

from fastapi import UploadFile

from app.core.exceptions import ValidationError
from app.core.telemetry import instrument
from app.repository import ActionRepository
from app.schemas.action_schema import BaseActionSchema
from app.schemas.action_schema import CompleteActionSchema
from app.services.base_service import BaseService


@instrument
class ActionService(BaseService):
    def __init__(self, action_repository: ActionRepository) -> None:
        super().__init__(action_repository)

    async def add(self, user_id: UUID, schema: BaseActionSchema, **kwargs):  # type: ignore
        input_schema = CompleteActionSchema(**schema.model_dump(), user_id=user_id)
        return await self._repository.create(input_schema, **kwargs)

    async def upload_file(self, id: UUID, file: UploadFile, **kwargs):  # type: ignore
        allowed_types = [
            "application/x-yaml",
            "text/yaml",
            "application/jmes",
            "text/jmes",
            "application/yaml",
            "application/yml",
        ]
        if file.content_type not in allowed_types:
            raise ValidationError(detail="Invalid file type. Allowed types are YAML and JMESPath files.")

        file_content = await file.read()
        base64_content = base64.b64encode(file_content).decode("utf-8")

        return await self._repository.update_attr(id, "file_mapping", base64_content)
