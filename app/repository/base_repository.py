from typing import Any
from typing import Union
from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import exceptions
from app.core.telemetry import instrument
from app.core.telemetry import logger
from app.schemas.base_schema import FindBase


@instrument(pyroscope_tagging=True)
class BaseRepository:
    def __init__(self, session: AsyncSession, model) -> None:
        self.session = session
        self.model = model

    async def get_order_by(self, schema):
        try:
            return (
                getattr(self.model, schema.ordering[1:]).desc()
                if schema.ordering.startswith("-")
                else getattr(self.model, schema.ordering).asc()
            )
        except AttributeError:
            raise exceptions.validation_error(f"unprocessable entity: attribute '{schema.ordering}' does not exist")

    async def get_model_by_id(
        self, session: AsyncSession, id: Union[UUID, int], use_select: bool = False, eager: bool = False
    ):
        logger.debug(f"Fetching {self.model.__name__} with ID {id} | select={use_select}, eager={eager}")
        if not (use_select and eager):
            return await self.session.get(self.model, id)

        query = select(self.model).where(self.model.id == id)
        if eager:
            for eager_relation in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager_relation)))

        result = await self.session.execute(query)
        return result.scalars().first()

    def get_compiled_query(self, query: select) -> str:
        return str(query.compile(compile_kwargs={"literal_binds": True}))

    async def read_by_options(self, schema: FindBase, eager: bool = False, unique: bool = False):
        logger.debug(f"Reading {self.model.__name__} by options: {schema.model_dump(exclude_unset=True)}")
        order_query = await self.get_order_by(schema)
        query = select(self.model).order_by(order_query)
        if eager:
            for eager_relation in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager_relation)))
        if schema.page_size != "all":
            query = query.offset((schema.page - 1) * (schema.page_size)).limit(int(schema.page_size))

        if schema.created_before:
            query = query.where(self.model.created_at < schema.created_before)

        if schema.created_on_or_before:
            query = query.where(self.model.created_at <= schema.created_on_or_before)

        if schema.created_after:
            query = query.where(self.model.created_at > schema.created_after)

        if schema.created_on_or_after:
            query = query.where(self.model.created_at >= schema.created_on_or_after)

        query = await self.session.execute(query)
        if unique:
            query = query.unique()
        result = query.scalars().all()
        logger.info(f"Found {len(result)} records for {self.model.__name__}")
        return {
            "data": result,
            "metadata": {
                "page": schema.page,
                "page_size": schema.page_size,
                "ordering": schema.ordering,
                "total_count": len(result),
                "created_before": schema.created_before,
                "created_on_or_before": schema.created_on_or_before,
                "created_after": schema.created_after,
                "created_on_or_after": schema.created_on_or_after,
            },
        }

    async def read_by_id(self, id: Union[UUID, int], eager: bool = False, use_select: bool = False):
        logger.debug(f"Reading {self.model.__name__} by ID: {id}")
        result = await self.get_model_by_id(self.session, id, eager, use_select)
        if not result:
            raise exceptions.not_found(detail=f"Resource with id={id} not found")
        return result

    async def read_by_email(self, email: EmailStr, unique: bool = False):
        logger.debug(f"Reading {self.model.__name__} by email: {email}")
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        if unique:
            result = result.unique()
        user = result.scalars().all()
        logger.info(f"Found {len(user)} entries with email={email}")
        return user

    async def create(self, schema: BaseModel):
        logger.debug(f"Creating {self.model.__name__} with data: {schema.model_dump(exclude_unset=True)}")
        model = self.model(**schema.model_dump())
        try:
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            logger.info(f"{self.model.__name__} created with ID {model.id}")
        except IntegrityError:
            raise exceptions.duplicated_error(detail=f"{self.model.__tablename__.capitalize()[:-1]} already registered")
        except Exception as error:
            raise exceptions.bad_request(str(error))
        return model

    async def update(self, id: Union[UUID, int], schema: BaseModel, use_select: bool = True):
        schema = schema.model_dump(exclude_unset=True)
        logger.debug(f"Updating {self.model.__name__} ID={id} with data: {schema}")
        model = await self.get_model_by_id(self.session, id, use_select)
        if not model:
            raise exceptions.not_found(detail=f"Resource with id={id} not found")
        if schema == {attr: getattr(model, attr) for attr in schema.keys()}:
            raise exceptions.bad_request(
                detail="Update aborted: no changes were provided or values are identical to existing ones"
            )

        for key, value in schema.items():
            setattr(model, key, value)

        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        logger.info(f"{self.model.__name__} with ID={id} successfully updated")
        return model

    async def update_attr(self, id: Union[UUID, int], column: str, value: Any, use_select: bool = False):
        logger.debug(f"Updating column '{column}' of {self.model.__name__} ID={id} with value: {value}")
        result = await self.get_model_by_id(self.session, id, use_select)
        if not result:
            raise exceptions.not_found(detail=f"Resource with id={id} not found")
        if value == getattr(result, column):
            raise exceptions.bad_request(detail="No changes detected")

        stmt = update(self.model).where(self.model.id == id).values({column: value})
        try:
            await self.session.execute(stmt)
            await self.session.commit()
            await self.session.refresh(result)
            logger.info(f"Updated '{column}' to '{value}' on model {self.model.__name__} (ID={id})")
            return result
        except IntegrityError as e:
            error_message = ":".join(str(e.orig).replace("\n", " ").split(":")[1:])
            raise exceptions.duplicated_error(detail=error_message)

    async def delete_by_id(self, id: Union[UUID, int], use_select: bool = False):
        logger.debug(f"Deleting {self.model.__name__} ID={id}")
        result = await self.get_model_by_id(self.session, id, use_select)
        if not result:
            raise exceptions.not_found(detail=f"not found id: {id}")
        await self.session.delete(result)
        await self.session.commit()
        logger.info(f"{self.model.__name__} with ID={id} successfully deleted")
