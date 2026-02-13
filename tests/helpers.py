from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import User
from app.models.models_enums import UserRoles
from tests.factories import create_factory_users
from tests.schemas import UserModelSetup
from tests.schemas import UserSchemaWithHashedPassword


base_auth_route: str = "/v1/auth"
base_users_url: str = "/v1/users"


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


async def setup_users_data(
    session: AsyncSession, model_args: List[UserModelSetup], **kwargs
) -> List[UserSchemaWithHashedPassword]:  # type: ignore
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


async def get_user_by_index(index: int = 0, token_header: Optional[str] = None):
    import httpx
    response = httpx.get(f"{base_users_url}/?ordering=username", headers=token_header)
    return response.json()["data"][index]
