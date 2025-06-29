from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict

from app.schemas.base_schema import FindModelResult
from app.schemas.base_schema import ModelBaseInfo


class BaseActionSchema(BaseModel):
    name: str = "test"
    url: str = "https://services-uat.bees-platform.dev/api/"
    path_url: str = "v1/data-ingestion-relay-service/v1"
    body_version: str = "v1"
    schedule: str = "0 0 * * *"


class CompleteActionSchema(BaseActionSchema):
    user_id: UUID


class ActionSchema(CompleteActionSchema, ModelBaseInfo):
    model_config = ConfigDict(from_attributes=True)
    file_mapping: Optional[str] = None


class BaseActionUpdateSchema(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    path_url: Optional[str] = None
    body_version: Optional[str] = None
    schedule: Optional[str] = None


class ActionUpdateSchema(BaseActionUpdateSchema):
    file_mapping: Optional[str] = None


class ActionListResultSchema(FindModelResult):
    data: List[ActionSchema]
