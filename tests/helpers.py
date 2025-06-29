from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID

import factory
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import User
from app.models.models_enums import UserRoles
from tests.factories import create_factory_users
from tests.schemas import UserModelSetup
from tests.schemas import UserSchemaWithHashedPassword

base_auth_route: str = "/v1/auth"
base_users_url: str = "/v1/user"


def validate_datetime(data_string):
    try:
        datetime.strptime(data_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        return True
    except ValueError:
        try:
            datetime.strptime(data_string, "%Y-%m-%dT%H:%M:%S")
            return True
        except ValueError:
            return False


async def add_models_generic(
    session: AsyncSession,
    factory: factory.Factory,
    schema_class: Optional[BaseModel] = None,
    qty: int = 1,
    index: Optional[int] = None,
    get_model: bool = False,
    **kwargs,
):
    models = factory.create_batch(qty, **kwargs)
    session.add_all(models)
    await session.commit()

    results = []
    for m in models:
        await session.refresh(m)
        if get_model or not schema_class:
            results.append(m)
        else:
            results.append(schema_class.model_validate(m))

    if index is not None:
        return results[index]
    return results


async def add_users_models(
    session: AsyncSession,
    users_qty: int = 1,
    user_role: UserRoles = UserRoles.BASE_USER,
    is_active=True,
    index: Optional[int] = None,
    get_model: bool = False,
) -> Union[
    List[Union[UserSchemaWithHashedPassword, User]],
    UserSchemaWithHashedPassword,
    User,
]:
    return_users: List[Union[UserSchemaWithHashedPassword, User]] = []
    users = create_factory_users(users_qty=users_qty, user_role=user_role, is_active=is_active)
    password_list = [factory_model.password for factory_model in users]
    for user in users:
        user.password = get_password_hash(user.password)
    session.add_all(users)
    await session.commit()
    for count, user in enumerate(users):
        await session.refresh(user)
        if get_model:
            return_users.append(user)
            continue
        return_users.append(
            UserSchemaWithHashedPassword(
                id=user.id,
                created_at=user.created_at,
                updated_at=user.updated_at,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                role=user.role,
                password=password_list[count],
                hashed_password=user.password,
            )
        )

    if index is not None:
        return return_users[index]
    return return_users


async def setup_users_data(session: AsyncSession, model_args: List[UserModelSetup], **kwargs):
    return_list: List[UserSchemaWithHashedPassword] = []
    for user_setup in model_args:
        user_list = await add_users_models(
            session,
            users_qty=user_setup.qty,
            user_role=user_setup.role,
            is_active=user_setup.is_active,
            **kwargs,
        )
        return_list.append(*user_list)
    return return_list


async def token(client, session: AsyncSession, base_auth_route: str = "/v1/auth", **kwargs):
    user = await add_users_models(session=session, index=0, **kwargs)
    response = await client.post(
        f"{base_auth_route}/sign-in",
        json={"email": user.email, "password": user.password},  # type: ignore
    )  # type: ignore
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def get_user_token(client: AsyncClient, user: UserSchemaWithHashedPassword) -> Dict[str, str]:
    response = await client.post(
        f"{base_auth_route}/sign-in",
        json={"email": user.email, "password": user.password},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def get_user_by_index(client, index: int = 0, token_header: Optional[str] = None):
    response = await client.get(f"{base_users_url}/?ordering=username", headers=token_header)
    return response.json()["data"][index]


async def get_token_by_user_id(user_id: UUID, client: AsyncClient, session: AsyncSession) -> Dict[str, str]:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User with id {user_id} not found.")

    test_password = "password"
    response = await client.post(
        f"{base_auth_route}/sign-in",
        json={"email": user.email, "password": test_password},
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get token for user {user_id}: {response.text}")

    return {"Authorization": f"Bearer {response.json()['access_token']}"}
