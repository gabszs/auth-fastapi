from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from app.schemas.base_schema import FindModelResult
from app.schemas.base_schema import ModelBaseInfo


class BaseWebHookSchema(BaseModel):
    action_id: UUID
    name: str = "test"


class CompleteWebHookSchema(BaseWebHookSchema):
    is_active: bool


class WebHookSchema(CompleteWebHookSchema, ModelBaseInfo):
    model_config = ConfigDict(from_attributes=True)


class WebHookUpdateSchema(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class WebHookListResultSchema(FindModelResult):
    data: List[WebHookSchema]
