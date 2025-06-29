from app.core.security import get_password_hash
from app.core.telemetry import instrument
from app.repository import UserRepository
from app.schemas.user_schema import BaseUserWithPasswordSchema
from app.services.base_service import BaseService


@instrument
class UserService(BaseService):
    def __init__(self, user_repository: UserRepository) -> None:
        super().__init__(user_repository)

    async def add(self, user_schema: BaseUserWithPasswordSchema):  # type: ignore
        user_schema.password = get_password_hash(user_schema.password)
        created_user = await self._repository.create(user_schema)
        delattr(created_user, "password")
        return created_user

    # will come here later, but for now only admin can touch this method
    # async def remove_by_id(self, id: Union[UUID, int], current_user: UserModel):
    #     return await self._repository.delete_by_id(id)
