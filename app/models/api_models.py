from typing import ClassVar
from typing import List
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base_model import Base
from app.models.models_enums import UserRoles


class User(Base):
    __tablename__ = "users"

    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)

    actions: Mapped[List["Action"]] = relationship(init=False)
    api_keys: Mapped[List["ApiKey"]] = relationship(init=False)

    role: Mapped[UserRoles] = mapped_column(default=UserRoles.BASE_USER, server_default=UserRoles.BASE_USER)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="True")


class ApiKey(Base):
    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    token: Mapped[str] = mapped_column(unique=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="api_keys", init=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    eagers: ClassVar[List[str]] = ["user"]


class Action(Base):
    __tablename__ = "actions"

    name: Mapped[str] = mapped_column(unique=True)
    url: Mapped[str]
    path_url: Mapped[str]
    body_version: Mapped[str]

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    webhook: Mapped[Optional["WebHook"]] = relationship(
        back_populates="action", uselist=False, cascade="all, delete-orphan", init=False
    )

    file_mapping: Mapped[Optional[str]] = mapped_column(nullable=True, default=None)
    schedule: Mapped[Optional[str]] = mapped_column(nullable=True, default=None)


class WebHook(Base):
    __tablename__ = "webhooks"
    __table_args__ = (UniqueConstraint("action_id"),)

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    action_id: Mapped[UUID] = mapped_column(ForeignKey("actions.id"), unique=True, nullable=False)
    action: Mapped["Action"] = relationship(back_populates="webhook", init=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    eagers: ClassVar[List[str]] = ["action"]
