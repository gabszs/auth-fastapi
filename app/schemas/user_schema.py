from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.models.models_enums import UserRoles
from app.schemas.base_schema import FindModelResult
from app.schemas.base_schema import ModelBaseInfo


class BaseUserSchema(BaseModel):
    email: EmailStr = Field(default="test@test.com")
    username: str = Field(default="test")


class BaseUserWithPasswordSchema(BaseUserSchema):
    password: str = Field(default="test")


class UserSchema(BaseUserSchema, ModelBaseInfo):
    model_config = ConfigDict(from_attributes=True)
    is_active: bool
    role: UserRoles


class UserUpdateSchema(BaseModel):
    email: Optional[EmailStr]
    username: Optional[str]
    is_active: Optional[bool]


class UserListResultSchema(FindModelResult):
    data: List[UserSchema]


class UserWithCleanPasswordSchema(BaseUserWithPasswordSchema):
    clean_password: str
