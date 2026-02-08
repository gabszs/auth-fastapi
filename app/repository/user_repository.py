from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import exceptions
from app.core.telemetry import instrument
from app.models import User
from app.repository.base_repository import BaseRepository


@instrument(pyroscope_tagging=True)
class UserRepository(BaseRepository):
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        super().__init__(session, User)

    async def create(self, schema):
        model = self.model(**schema.model_dump())
        try:
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
        except IntegrityError as e:
            if "Key (email)" in str(e.orig):
                raise exceptions.duplicated_error(detail="Email already registered")
            if "Key (username)" in str(e.orig):
                raise exceptions.duplicated_error(detail="Username already registered")
            raise exceptions.duplicated_error(detail=f"{self.model.__tablename__.capitalize()[:-1]} already registered")
        return model
