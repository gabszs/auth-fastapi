import io
from typing import AsyncGenerator
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Union
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import SessionTransaction

from app.core.settings import settings
from app.main import app
from app.models import Base
from app.models import User
from app.models.models_enums import UserRoles
from app.schemas.action_schema import ActionSchema
from app.schemas.api_key_schema import ApiKeySchema
from app.schemas.webhook_schema import WebHookSchema
from tests.factories import ActionFactory
from tests.factories import ApiKeyFactory
from tests.factories import UserFactory
from tests.factories import WebHookFactory
from tests.helpers import add_models_generic
from tests.helpers import add_users_models
from tests.helpers import get_token_by_user_id
from tests.helpers import token
from tests.schemas import UserModelSetup
from tests.schemas import UserSchemaWithHashedPassword
from tests.schemas import UserWithToken
from tests.schemas import WebHookWithUserIdSchema


if settings.TEST_DATABASE_URL is None:
    raise KeyError("Variável de ambiente 'TEST_DATABASE_URL' não está setada.")
sync_db_url = settings.TEST_DATABASE_URL.replace("+asyncpg", "")


@pytest.fixture
def random_uuid() -> UUID:
    return uuid4()


@pytest.fixture
def batch_setup_users() -> List[UserModelSetup]:
    setup_list: List[UserModelSetup] = []
    for role in UserRoles:
        setup_list.append(UserModelSetup(is_active=True, role=role))
        setup_list.append(UserModelSetup(is_active=False, role=role))
    return setup_list


@pytest.fixture
def default_search_options() -> Dict[str, Optional[Union[str, int]]]:
    return {
        "ordering": "id",
        "page": 1,
        "page_size": "all",
    }


@pytest.fixture
def default_created_search_options() -> Dict[str, Optional[Union[str, int]]]:
    return {
        "ordering": "created_at",
        "page": 1,
        "page_size": "all",
    }


@pytest.fixture
def default_username_search_options() -> Dict[str, Optional[Union[str, int]]]:
    return {
        "ordering": "username",
        "page": 1,
        "page_size": "all",
    }


@pytest.fixture
def factory_user() -> UserFactory:
    return UserFactory()


@pytest.fixture
def factory_webhook() -> WebHookFactory:
    return WebHookFactory()


@pytest.fixture
def factory_api_key() -> UserFactory:
    return ApiKeyFactory()


@pytest.fixture
def factory_action() -> ActionFactory:
    return ActionFactory()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncGenerator:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        yield client


@pytest.fixture(autouse=True, scope="session")
def setup_cache():
    FastAPICache.init(InMemoryBackend(), cache_status_header=settings.CACHE_STATUS_HEADER, expire=360)


@pytest.fixture(scope="session")
def setup_db() -> Generator:
    engine = create_engine(sync_db_url)
    conn = engine.connect()
    conn.execute(text("commit"))

    try:
        conn.execute(text("drop database test"))
    except SQLAlchemyError:
        pass
    finally:
        conn.close()

    conn = engine.connect()

    conn.execute(text("commit"))
    conn.execute(text("create database test"))
    conn.close()

    yield

    conn = engine.connect()
    conn.execute(text("commit"))
    try:
        conn.execute(text("drop database test"))
    except SQLAlchemyError:
        pass
    conn.close()
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(setup_db: Generator) -> Generator:
    engine = create_engine(sync_db_url)

    with engine.begin():
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        yield
        Base.metadata.drop_all(engine)

    engine.dispose()


@pytest.fixture
async def session() -> AsyncGenerator:
    async_engine = create_async_engine(settings.TEST_DATABASE_URL)

    async with async_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()
        AsyncSessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn,
            future=True,
        )

        async_session = AsyncSessionLocal()

        @event.listens_for(async_session.sync_session, "after_transaction_end")
        def end_savepoint(session: Session, transaction: SessionTransaction) -> None:
            if conn.closed:
                return
            if not conn.in_nested_transaction():
                if conn.sync_connection:
                    conn.sync_connection.begin_nested()

        def test_get_session() -> Generator:
            try:
                yield AsyncSessionLocal()
            except SQLAlchemyError:
                pass

        from app.core.database import sessionmanager

        app.dependency_overrides[sessionmanager.session] = test_get_session

        yield async_session
        await async_session.close()
        await conn.rollback()

    await async_engine.dispose()


@pytest.fixture()
async def normal_user_token(client: AsyncClient, session: AsyncSession) -> Dict[str, str]:
    return await token(client, session)


@pytest.fixture()
async def user_with_token(client: AsyncClient, session: AsyncSession) -> UserWithToken:
    user = await add_users_models(session, index=0)
    token = await get_token_by_user_id(user.id, client, session)  # type: ignore
    return UserWithToken(**user.model_dump(), token=token)  # type: ignore


@pytest.fixture()
async def moderator_user_token(client: AsyncClient, session: AsyncSession) -> Dict[str, str]:
    return await token(client, session, user_role=UserRoles.MODERATOR)


@pytest.fixture()
async def admin_user_token(client: AsyncClient, session: AsyncSession) -> Dict[str, str]:
    return await token(client, session, user_role=UserRoles.ADMIN)


@pytest.fixture()
async def disable_normal_user_token(client: AsyncClient, session: AsyncSession) -> Dict[str, str]:
    return await token(client, session, user_role=UserRoles.MODERATOR, is_active=False)


@pytest.fixture()
async def normal_user(session: AsyncSession) -> List[Union[UserSchemaWithHashedPassword, User]]:
    return await add_users_models(session, index=0)


@pytest.fixture()
async def moderator_user(session: AsyncSession) -> List[Union[UserSchemaWithHashedPassword, User]]:
    return await add_users_models(session, index=0, user_role=UserRoles.MODERATOR)


@pytest.fixture()
async def admin_user(session: AsyncSession) -> List[Union[UserSchemaWithHashedPassword, User]]:
    return await add_users_models(session, index=0, user_role=UserRoles.ADMIN)


@pytest.fixture()
async def disable_normal_user(session: AsyncSession) -> List[Union[UserSchemaWithHashedPassword, User]]:
    return await add_users_models(session, index=0, user_role=UserRoles.BASE_USER, is_active=False)


@pytest.fixture()
async def action(session: AsyncSession, normal_user):
    return await add_models_generic(session, ActionFactory, ActionSchema, index=0, user_id=normal_user.id)


@pytest.fixture()
async def other_action(session: AsyncSession, normal_user):
    return await add_models_generic(
        session,
        ActionFactory,
        ActionSchema,
        index=0,
        user_id=normal_user.id,
    )


@pytest.fixture()
async def multiple_action(session: AsyncSession, normal_user):
    return await add_models_generic(
        session,
        ActionFactory,
        ActionSchema,
        qty=4,
        user_id=normal_user.id,
    )


@pytest.fixture()
async def api_key(session: AsyncSession, normal_user):
    return await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=normal_user.id)


@pytest.fixture()
async def other_api_key(session: AsyncSession, normal_user):
    return await add_models_generic(
        session,
        ApiKeyFactory,
        ApiKeySchema,
        index=0,
        user_id=normal_user.id,
    )


@pytest.fixture()
async def multiple_api_key(session: AsyncSession, normal_user):
    return await add_models_generic(session, ApiKeyFactory, ApiKeySchema, qty=4, user_id=normal_user.id)


@pytest.fixture()
async def webhook(session: AsyncSession, action):
    webhook = await add_models_generic(session, WebHookFactory, WebHookSchema, index=0, action_id=action.id)
    return WebHookWithUserIdSchema(**webhook.model_dump(), user_id=action.user_id)


@pytest.fixture
def yaml_file() -> tuple:
    """Fixture that returns a YAML file ready to be sent in request"""
    yaml_content = """
version: "1.0"
mappings:
- source: "user.name"
    target: "userName"action_with_user
- type: "uppercase"
    field: "userName"
- type: "lowercase"
    field: "userEmail"
"""
    yaml_bytes = yaml_content.encode("utf-8")
    yaml_file_obj = io.BytesIO(yaml_bytes)

    return ("mapping.yaml", yaml_file_obj, "application/x-yaml")


@pytest.fixture
def jmes_file() -> tuple:
    """Fixture that returns a JMES file ready to be sent in request"""
    jmes_content = """
{
"user_name": "user.name",
"user_email": "user.email | lower(@)",
"user_id": "user.id",
"full_data": "{name: user.name, email: user.email, active: user.is_active}"
}
"""
    jmes_bytes = jmes_content.encode("utf-8")
    jmes_file_obj = io.BytesIO(jmes_bytes)

    return ("mapping.jmes", jmes_file_obj, "application/jmes")
