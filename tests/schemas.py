from typing import Dict
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.models_enums import UserRoles
from app.schemas.user_schema import UserSchema
from app.schemas.webhook_schema import WebHookSchema


class WebHookWithUserIdSchema(WebHookSchema):
    user_id: UUID


class UserModelSetup(BaseModel):
    qty: int = 1
    is_active: bool = True
    role: UserRoles = UserRoles.BASE_USER


class UserSchemaWithHashedPassword(UserSchema):
    password: Optional[str] = None
    hashed_password: Optional[str] = None


class UserWithToken(UserSchemaWithHashedPassword):
    token: Dict[str, str]
