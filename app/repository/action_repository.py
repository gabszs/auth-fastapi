from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import instrument
from app.models import Action
from app.repository.base_repository import BaseRepository


@instrument
class ActionRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Action)
