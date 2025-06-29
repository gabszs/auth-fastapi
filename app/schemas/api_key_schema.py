from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from app.schemas.base_schema import FindModelResult
from app.schemas.base_schema import ModelBaseInfo


class BaseApiKeySchema(BaseModel):
    user_id: UUID
    name: str = "test"


class CompleteApiKeySchema(BaseApiKeySchema):
    token: str
    is_active: bool


class ApiKeySchema(CompleteApiKeySchema, ModelBaseInfo):
    model_config = ConfigDict(from_attributes=True)


class ApiKeyUpdateSchema(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None


class ApiKeyListResultSchema(FindModelResult):
    data: List[ApiKeySchema]
