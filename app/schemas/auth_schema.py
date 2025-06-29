from datetime import datetime

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

from app.schemas.user_schema import UserSchema


class SignIn(BaseModel):
    email: EmailStr = Field(default="test@test.com")
    password: str = Field(default="test")


class SignUp(BaseModel):
    email: EmailStr
    password: str
    username: str


class Payload(BaseModel):
    id: str
    email: EmailStr
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str


class SignInResponse(BaseModel):
    access_token: str
    expiration: datetime
    user_info: UserSchema
