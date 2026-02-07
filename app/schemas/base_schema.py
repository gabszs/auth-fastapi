from datetime import datetime
from typing import Annotated
from typing import Any
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic import ValidationInfo
from pydantic._internal._model_construction import ModelMetaclass

from app.core.exceptions import exceptions
from app.core.settings import settings


class Message(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class NoContent(BaseModel):
    pass


class AllOptional(ModelMetaclass):
    def __new__(self, name, bases, namespaces, **kwargs):
        annotations = namespaces.get("__annotations__", {})
        for base in bases:
            annotations.update(base.__annotations__)
        for field in annotations:
            if not field.startswith("__"):
                annotations[field] = Optional[annotations[field]]
        namespaces["__annotations__"] = annotations
        return super().__new__(self, name, bases, namespaces, **kwargs)


class ModelBaseInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FindBase(BaseModel):
    ordering: str = settings.ORDERING
    page: Annotated[int, Field(gt=0)] = settings.PAGE
    page_size: Union[int, str] = settings.PAGE_SIZE
    created_before: Optional[datetime] = None
    created_on_or_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    created_on_or_after: Optional[datetime] = None

    @field_validator("page_size")
    @classmethod
    def page_size_field_validator(cls, value: Union[str, int], info: ValidationInfo):
        try:
            input = int(value)
            if input < 0:
                raise exceptions.validation_error("Page size must be a positive integer")
            return input
        except Exception as _:
            if value != "all":
                raise exceptions.validation_error("Page size must be 'all' or a positive integer")
            return value

    @model_validator(mode="after")
    def validate_date_ranges(self):
        if self.created_after is not None and self.created_on_or_after is not None:
            raise exceptions.validation_error(
                "CONFLICTING_DATE_FILTERS: Cannot use both created_after and created_on_or_after"
            )

        if self.created_before is not None and self.created_on_or_before is not None:
            raise exceptions.validation_error(
                "CONFLICTING_DATE_FILTERS: Cannot use both created_before and created_on_or_before"
            )

        start_date = self.created_after or self.created_on_or_after
        end_date = self.created_before or self.created_on_or_before

        if start_date is not None and end_date is not None and start_date >= end_date:
            raise exceptions.validation_error("INVALID_DATE_RANGE: Start date must be before end date")

        return self


class Metadata(FindBase):
    total_count: Optional[int]


class FindResult(BaseModel):
    data: Optional[List]
    metadata: Optional[Metadata]


class FindDateRange(BaseModel):
    created_at__lt: str
    created_at__lte: str
    created_at__gt: str
    created_at__gte: str


class FindModelResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    data: List[Any]
    metadata: Metadata


class Blank(BaseModel):
    pass
