from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.security import authorize
from app.models.models_enums import UserRoles


@pytest.fixture
def mock_function():
    return AsyncMock()


@pytest.mark.asyncio
async def test_authorize_with_valid_with_same_id_equals_true(mock_function):
    user = AsyncMock(role=UserRoles.BASE_USER, id=123)
    kwargs = {"current_user": user, "id": 123}
    decorated_func = authorize(role=[UserRoles.MODERATOR], allow_same_id=True)(mock_function)
    result = await decorated_func(**kwargs)
    assert result == mock_function.return_value


@pytest.mark.asyncio
async def test_authorize_with_admin(mock_function):
    user = AsyncMock(role=UserRoles.ADMIN, id=123)
    kwargs = {"current_user": user, "id": 123}
    decorated_func = authorize(role=[UserRoles.ADMIN])(mock_function)
    result = await decorated_func(**kwargs)
    assert result == mock_function.return_value


@pytest.mark.asyncio
async def test_authorize_with_invalid_role(mock_function):
    user = AsyncMock(role=UserRoles.BASE_USER, id=123)
    kwargs = {"current_user": user, "id": 123}
    decorated_func = authorize(role=[UserRoles.MODERATOR])(mock_function)
    with pytest.raises(HTTPException):
        await decorated_func(**kwargs)


@pytest.mark.asyncio
async def test_authorize_with_invalid_id(mock_function):
    user = AsyncMock(role=UserRoles.BASE_USER, id=123)
    kwargs = {"current_user": user, "id": 456}
    decorated_func = authorize(role=[UserRoles.MODERATOR], allow_same_id=True)(mock_function)
    with pytest.raises(HTTPException):
        await decorated_func(**kwargs)


@pytest.mark.asyncio
async def test_authorize_without_same_id(mock_function):
    user = AsyncMock(role=UserRoles.BASE_USER, id=123)
    kwargs = {"current_user": user, "id": 124}
    decorated_func = authorize(role=[UserRoles.MODERATOR], allow_same_id=False)(mock_function)
    with pytest.raises(HTTPException):
        await decorated_func(**kwargs)
