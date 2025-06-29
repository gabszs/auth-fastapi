from typing import Any
from typing import Union
from uuid import UUID

from fastapi_cache import FastAPICache
from pydantic import BaseModel

from app.core.telemetry import instrument
from app.repository.base_repository import BaseRepository
from app.schemas.base_schema import FindBase


@instrument
class BaseService:
    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

    async def invalidate_cache(self, id: Union[UUID, int]) -> None:
        try:
            await FastAPICache.clear(key=f"{self.__class__.__name__}:{id}")
        except KeyError:
            pass

    async def get_list(self, schema: FindBase, **kwargs):
        return await self._repository.read_by_options(schema, **kwargs)

    async def get_by_id(self, id: Union[UUID, int], **kwargs):
        return await self._repository.read_by_id(id, **kwargs)

    async def add(self, schema: BaseModel, **kwargs):
        return await self._repository.create(schema, **kwargs)

    async def patch(self, id: Union[UUID, int], schema: BaseModel, **kwargs):
        await self.invalidate_cache(id)
        return await self._repository.update(id, schema, **kwargs)

    async def patch_attr(self, id: Union[UUID, int], attr: str, value, **kwargs):
        await self.invalidate_cache(id)
        return await self._repository.update_attr(id, attr, value, **kwargs)

    async def remove_by_id(self, id: Union[UUID, int], **kwargs):
        await self.invalidate_cache(id)
        return await self._repository.delete_by_id(id, **kwargs)

    async def get_by_param(self, param: str, value: Any, **kwargs):
        return await self._repository.get_by_key(param, value, **kwargs)
