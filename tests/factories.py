import random
from typing import Any
from typing import Dict

import factory
import ulid
from factory.base import StubObject

from app.models import Action
from app.models import ApiKey
from app.models import User
from app.models import WebHook
from app.models.models_enums import UserRoles


def generate_cron():
    minute = random.randint(0, 59)
    hour = random.randint(0, 23)
    return f"{minute} {hour} * * *"


def convert_dict_from_stub(stub: StubObject) -> Dict[str, Any]:
    stub_dict = stub.__dict__
    for key, value in stub_dict.items():
        if isinstance(value, StubObject):
            stub_dict[key] = convert_dict_from_stub(value)
    return stub_dict


def factory_object_to_dict(factory_instance):
    attributes = factory_instance.__dict__
    attributes.pop("_declarations", None)
    return attributes


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda x: f"user_{x}")
    email = factory.LazyAttribute(lambda x: f"{x.username}@test.com")
    password = "password"
    role = UserRoles.BASE_USER
    is_active = None


class ApiKeyFactory(factory.Factory):
    class Meta:
        model = ApiKey

    name = factory.Sequence(lambda x: f"api_key_{x}")
    token = factory.LazyAttribute(lambda obj: f"token_{obj.name}_{ulid.new()}")
    is_active = True
    user_id = None


class ActionFactory(factory.Factory):
    class Meta:
        model = Action

    name = factory.Sequence(lambda x: f"action_{x}")
    url = factory.LazyAttribute(lambda x: f"https://{x.name}.com")
    path_url = factory.LazyAttribute(lambda obj: f"{obj.name}/v1/")
    body_version = factory.LazyAttribute(lambda obj: f"{obj.name}/v1")
    file_mapping = factory.LazyAttribute(lambda obj: f"{obj.name}.yaml")
    schedule = factory.LazyFunction(generate_cron)
    user_id = None


class WebHookFactory(factory.Factory):
    class Meta:
        model = WebHook

    name = factory.Sequence(lambda x: f"webhook_{x}")
    action_id = None
    is_active = True


def create_factory_users(
    users_qty: int = 1,
    user_role: UserRoles = UserRoles.BASE_USER,
    is_active=True,
):
    return UserFactory.create_batch(users_qty, role=user_role, is_active=is_active)
