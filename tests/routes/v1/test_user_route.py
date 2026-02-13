from typing import List
from urllib.parse import urlencode
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.helpers import get_user_by_index
from tests.helpers import get_user_token
from tests.helpers import setup_users_data
from tests.helpers import validate_datetime
from tests.schemas import UserSchemaWithHashedPassword

base_users_url: str = "/v1/users"
datetime_params = {
    "created_after": None,
    "created_before": None,
    "created_on_or_after": None,
    "created_on_or_before": None,
}


async def get_token_user(client: AsyncClient, token_header: str) -> UserSchemaWithHashedPassword:
    user = await get_user_by_index(client, token_header=token_header)
    return UserSchemaWithHashedPassword(**user, password="", hashed_password="")


async def get_input_complete_list(
    client: AsyncClient,
    token_header: str,
    setup_users: List[UserSchemaWithHashedPassword],
) -> List[UserSchemaWithHashedPassword]:
    user = await get_token_user(client, token_header)
    setup_users.insert(0, user)
    return setup_users


@pytest.mark.anyio
async def test_get_all_users_should_return_200_OK_GET(
    session,
    client,
    default_username_search_options,
    batch_setup_users,
    moderator_user_token,
):
    expected_lenght = (
        len(batch_setup_users) + 1
    )  # this plus one becouse of token_fixture, that adds one before this batch save
    setup_users = await setup_users_data(session=session, model_args=batch_setup_users)
    setup_users = await get_input_complete_list(client, moderator_user_token, setup_users)
    response = await client.get(
        f"{base_users_url}?{urlencode(default_username_search_options)}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    users_json = response_json["data"]
    assert response.status_code == 200
    assert len(users_json) == expected_lenght
    assert (
        response_json["metadata"]
        == default_username_search_options | {"total_count": expected_lenght} | datetime_params
    )
    assert all(
        [
            user.username == users_json[count].get("username") and user.email == users_json[count].get("email")
            for count, user in enumerate(setup_users)
        ]
    )

    assert all([validate_datetime(user["created_at"]) for user in users_json])
    assert all([validate_datetime(user["updated_at"]) for user in users_json])


# # hard test
@pytest.mark.anyio
async def test_get_all_users_with_page_size_should_return_200_OK_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_find_parameters = {"ordering": "username", "page": 1, "page_size": 5}
    setup_users = await setup_users_data(session=session, model_args=batch_setup_users)
    setup_users = await get_input_complete_list(client, moderator_user_token, setup_users)

    response = await client.get(
        f"{base_users_url}?{urlencode(query_find_parameters)}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert all(
        [
            user.username == response_json["data"][count].get("username")
            and user.email == response_json["data"][count].get("email")
            for count, user in enumerate(setup_users[: query_find_parameters["page_size"]])
        ]
    )
    assert len(response_json["data"]) == 5
    assert response_json["metadata"] == query_find_parameters | {"total_count": 5} | datetime_params
    assert all([validate_datetime(user["created_at"]) for user in response_json["data"]])
    assert all([validate_datetime(user["updated_at"]) for user in response_json["data"]])


# hard test
@pytest.mark.anyio
async def test_get_all_users_with_pagination_should_return_200_OK_GET(
    session, client, batch_setup_users, moderator_user_token
):
    page_size = 3
    page = 2
    ordering = "username"
    query_find_parameters = {
        "ordering": ordering,
        "page": page,
        "page_size": page_size,
    }
    setup_users = await setup_users_data(session=session, model_args=batch_setup_users)
    setup_users = await get_input_complete_list(client, moderator_user_token, setup_users)

    response = await client.get(
        f"{base_users_url}?{urlencode(query_find_parameters)}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert all(
        [
            user.username == response_json["data"][count].get("username")
            and user.email == response_json["data"][count].get("email")
            for count, user in enumerate(setup_users[page_size : page_size * page])
        ]
    )
    assert len(response_json["data"]) == query_find_parameters["page_size"]
    assert (
        response_json["metadata"]
        == query_find_parameters | {"total_count": query_find_parameters["page_size"]} | datetime_params
    )
    assert all([validate_datetime(user["created_at"]) for user in response_json["data"]])
    assert all([validate_datetime(user["updated_at"]) for user in response_json["data"]])


# hard test
@pytest.mark.anyio
async def test_get_user_by_id_should_return_200_OK_GET(session, client, moderator_user, batch_setup_users):
    moderator_token = await get_user_token(client, moderator_user)
    response = await client.get(
        f"{base_users_url}/{moderator_user.id}",
        headers=moderator_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == moderator_user.id
    assert response_json["is_active"] is True
    assert response_json["role"] == moderator_user.role
    assert response_json["email"] == moderator_user.email
    assert response_json["username"] == moderator_user.username
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_get_user_by_id_should_return_404_NOT_FOUND_GET(session, random_uuid, client, moderator_user_token):
    response = await client.get(
        f"{base_users_url}/{random_uuid}",
        headers=moderator_user_token,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}


@pytest.mark.anyio
async def test_create_normal_user_should_return_422_unprocessable_entity_POST(client):
    response = await client.post(
        f"{base_users_url}",
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_normal_user_should_return_201_POST(client, session, factory_user):
    response = await client.post(
        f"{base_users_url}",
        json={
            "email": factory_user.email,
            "username": factory_user.username,
            "password": factory_user.password,
        },
    )
    response_json = response.json()

    assert response.status_code == 201
    assert UUID(response_json["id"])
    assert response_json["email"] == factory_user.email
    assert response_json["username"] == factory_user.username
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_create_normal_user_should_return_409_email_already_registered_POST(client, session, normal_user):
    response = await client.post(
        f"{base_users_url}",
        json={
            "email": normal_user.email,
            "username": "different_username",
            "password": normal_user.password,
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.anyio
async def test_create_normal_user_should_return_409_username_already_registered_POST(client, session, normal_user):
    response = await client.post(
        f"{base_users_url}",
        json={
            "email": "different@email.com",
            "username": normal_user.username,
            "password": normal_user.password,
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already registered"}


@pytest.mark.anyio
async def test_disable_user_should_return_200_OK_DELETE(session, client, normal_user, moderator_user_token):
    token = await get_user_token(client, normal_user)
    response = await client.patch(f"{base_users_url}/disable/{normal_user.id}", headers=token)
    response_json = response.json()
    modified_user = await get_user_by_index(client, 0, token_header=moderator_user_token)

    assert response.status_code == 200
    assert response_json == {"detail": "User has been desabled successfully"}
    assert normal_user.is_active is True
    assert modified_user["is_active"] is False
    assert modified_user["email"] == normal_user.email
    assert modified_user["username"] == normal_user.username
    assert modified_user["id"] == str(normal_user.id)


@pytest.mark.anyio
async def test_disable_different_user_should_return_403_FORBIDDEN_DELETE(
    session, client, normal_user, normal_user_token
):
    response = await client.patch(
        f"{base_users_url}/disable/{normal_user.id}",
        headers=normal_user_token,
    )
    response_json = response.json()

    assert response.status_code == 403
    assert response_json == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_enable_user_user_should_return_200_OK_PATCH(session, client, disable_normal_user, moderator_user_token):
    token = await get_user_token(client, disable_normal_user)
    response = await client.patch(
        f"{base_users_url}/enable_user/{disable_normal_user.id}",
        headers=token,
    )
    response_json = response.json()
    modified_user = await get_user_by_index(client, 0, token_header=moderator_user_token)

    assert response.status_code == 200
    assert response_json == {"detail": "User has been enabled successfully"}
    assert disable_normal_user.is_active is False
    assert modified_user["is_active"] is True
    assert modified_user["email"] == disable_normal_user.email
    assert modified_user["username"] == disable_normal_user.username
    assert modified_user["id"] == str(disable_normal_user.id)


@pytest.mark.anyio
async def test_enable_user_different_user_should_return_403_FORBIDDEN_PATCH(
    session, client, normal_user, normal_user_token
):
    response = await client.patch(
        f"{base_users_url}/enable_user/{normal_user.id}",
        headers=normal_user_token,
    )
    response_json = response.json()
    assert response.status_code == 403
    assert response_json == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_delete_user_should_return_200_OK_DELETE(session, client, normal_user, admin_user_token):
    response = await client.delete(f"{base_users_url}/{normal_user.id}", headers=admin_user_token)
    get_users_response = await client.get(
        f"{base_users_url}?offset=0&limit=100",
        headers=admin_user_token,
    )

    assert response.status_code == 204
    assert get_users_response.status_code == 200
    assert len(get_users_response.json()["data"]) == 1


@pytest.mark.anyio
async def test_delete_different_authorization_should_return_403_FORBIDDEN_DELETE(
    session, client, normal_user, normal_user_token
):
    response = await client.delete(
        f"{base_users_url}/{normal_user.id}",
        headers=normal_user_token,
    )
    response_json = response.json()
    assert response.status_code == 403
    assert response_json == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_put_user_should_return_200_OK_PUT(session, client, factory_user, normal_user):
    token = await get_user_token(client, normal_user)
    different_user = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": False,
    }

    response = await client.put(
        f"{base_users_url}/{normal_user.id}",
        headers=token,
        json=different_user,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])
    assert all([response_json[key] == value for key, value in different_user.items()])


@pytest.mark.anyio
async def test_put_user_with_admin_should_return_200_OK_PUT(
    session, client, factory_user, normal_user, admin_user_token
):
    different_user = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": False,
    }

    response = await client.put(
        f"{base_users_url}/{normal_user.id}",
        headers=admin_user_token,
        json=different_user,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])
    assert all([response_json[key] == value for key, value in different_user.items()])


@pytest.mark.anyio
async def test_put_user_should_return_403_FORBIDDEN_PUT(session, client, factory_user, normal_user, moderator_user):
    token = await get_user_token(client, normal_user)

    different_user = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": False,
        "is_superuser": True,
    }

    response = await client.put(
        f"{base_users_url}/{moderator_user.id}",
        headers=token,
        json=different_user,
    )

    assert response.json() == {"detail": "Not enough permissions"}
    assert response.status_code == 403


# =====================
# CACHE BEHAVIOR TESTS
# =====================


@pytest.mark.anyio
async def test_get_user_by_id_cache_miss_then_hit(client: AsyncClient, normal_user, admin_user_token):
    """Test that first request is MISS and subsequent requests are HIT"""
    user_id = normal_user.id
    url = f"{base_users_url}/{user_id}"

    # First request should be MISS
    response_1 = await client.get(url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"
    assert "cache-control" in response_1.headers
    assert "etag" in response_1.headers
    data_1 = response_1.json()

    # Second request should be HIT
    response_2 = await client.get(url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"
    assert "cache-control" in response_2.headers
    assert "etag" in response_2.headers
    data_2 = response_2.json()

    # Data should be identical
    assert data_1 == data_2
    assert UUID(data_1["id"]) == user_id


@pytest.mark.anyio
async def test_get_user_by_id_cache_headers_present(client: AsyncClient, normal_user, admin_user_token):
    """Test that cache-related headers are present"""
    user_id = normal_user.id
    url = f"{base_users_url}/{user_id}"

    response = await client.get(url, headers=admin_user_token)

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "max-age=360" in response.headers.get("cache-control", "")
    assert "etag" in response.headers
    assert response.headers.get("etag").startswith("W/")
    assert "x-api-cache" in response.headers


@pytest.mark.anyio
async def test_get_user_by_id_cache_different_users_different_cache(
    client: AsyncClient, normal_user, moderator_user, admin_user_token
):
    """Test that different users have different cache entries"""
    user_1_id = normal_user.id
    user_2_id = moderator_user.id

    url_1 = f"{base_users_url}/{user_1_id}"
    url_2 = f"{base_users_url}/{user_2_id}"

    # First user - should be MISS
    response_1 = await client.get(url_1, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second user - should be MISS (different cache key)
    response_2 = await client.get(url_2, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "MISS"

    # First user again - should be HIT
    response_1_again = await client.get(url_1, headers=admin_user_token)
    assert response_1_again.status_code == 200
    assert response_1_again.headers.get("x-api-cache") == "HIT"

    # Second user again - should be HIT
    response_2_again = await client.get(url_2, headers=admin_user_token)
    assert response_2_again.status_code == 200
    assert response_2_again.headers.get("x-api-cache") == "HIT"


@pytest.mark.anyio
async def test_get_user_by_id_cache_same_user_own_access(client: AsyncClient, normal_user):
    """Test that user can access their own data with cache behavior"""
    user_token = await get_user_token(client, normal_user)
    user_id = normal_user.id
    url = f"{base_users_url}/{user_id}"

    # First request - MISS
    response_1 = await client.get(url, headers=user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second request - HIT
    response_2 = await client.get(url, headers=user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # Data consistency check
    assert response_1.json() == response_2.json()


@pytest.mark.anyio
async def test_get_user_with_cache_behavior(client, normal_user, admin_user_token):
    user_id = normal_user.id
    url = f"/v1/users/{user_id}"

    response_1 = await client.get(url, headers=admin_user_token)
    assert response_1.status_code == 200
    data_1 = response_1.json()

    response_2 = await client.get(url, headers=admin_user_token)
    assert response_2.status_code == 200
    data_2 = response_2.json()

    assert data_1 == data_2


# ==========================
# CACHE INVALIDATION TESTS
# ==========================


@pytest.mark.anyio
async def test_cache_invalidation_after_put_update(client: AsyncClient, normal_user, factory_user, admin_user_token):
    """Test that cache is invalidated after PUT update"""
    user_id = normal_user.id
    url = f"{base_users_url}/{user_id}"

    # First GET - should be MISS and cached
    response_1 = await client.get(url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"
    original_data = response_1.json()

    # Second GET - should be HIT
    response_2 = await client.get(url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # PUT update
    update_data = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": False,
    }

    put_response = await client.put(url, headers=admin_user_token, json=update_data)
    assert put_response.status_code == 200

    # GET after PUT - should be MISS (cache invalidated)
    response_3 = await client.get(url, headers=admin_user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    updated_data = response_3.json()

    # Verify data was actually updated
    assert updated_data["email"] == factory_user.email
    assert updated_data["username"] == factory_user.username
    assert updated_data["is_active"] is False
    assert updated_data != original_data

    # Next GET should be HIT again
    response_4 = await client.get(url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"
    assert response_4.json() == updated_data


@pytest.mark.anyio
async def test_cache_invalidation_after_patch_disable_user(client: AsyncClient, normal_user, admin_user_token):
    """Test that cache is invalidated after PATCH disable operation"""
    user_id = normal_user.id
    get_url = f"{base_users_url}/{user_id}"
    patch_url = f"{base_users_url}/disable/{user_id}"

    # Get user token for the disable operation
    user_token = await get_user_token(client, normal_user)

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"
    assert response_1.json()["is_active"] is True

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # PATCH disable user
    patch_response = await client.patch(patch_url, headers=user_token)
    assert patch_response.status_code == 200
    assert patch_response.json() == {"detail": "User has been desabled successfully"}

    # GET after PATCH - should be MISS (cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    assert response_3.json()["is_active"] is False

    # Next GET should be HIT again
    response_4 = await client.get(get_url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"


@pytest.mark.anyio
async def test_cache_invalidation_after_patch_enable_user(client: AsyncClient, disable_normal_user, admin_user_token):
    """Test that cache is invalidated after PATCH enable operation"""
    user_id = disable_normal_user.id
    get_url = f"{base_users_url}/{user_id}"
    patch_url = f"{base_users_url}/enable_user/{user_id}"

    # Get user token for the enable operation
    user_token = await get_user_token(client, disable_normal_user)

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"
    assert response_1.json()["is_active"] is False

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # PATCH enable user
    patch_response = await client.patch(patch_url, headers=user_token)
    assert patch_response.status_code == 200
    assert patch_response.json() == {"detail": "User has been enabled successfully"}

    # GET after PATCH - should be MISS (cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    assert response_3.json()["is_active"] is True

    # Next GET should be HIT again
    response_4 = await client.get(get_url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"


@pytest.mark.anyio
async def test_cache_invalidation_after_delete_user(session, client: AsyncClient, normal_user, admin_user_token):
    """Test that cache is invalidated after DELETE operation"""
    user_id = normal_user.id
    get_url = f"{base_users_url}/{user_id}"
    delete_url = f"{base_users_url}/{user_id}"

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # DELETE user
    delete_response = await client.delete(delete_url, headers=admin_user_token)
    assert delete_response.status_code == 204

    # GET after DELETE - should return 404 (user deleted, cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 404
    assert response_3.json() == {"detail": f"Resource with id={user_id} not found"}


@pytest.mark.anyio
async def test_cache_not_invalidated_by_different_user_operations(
    client: AsyncClient, normal_user, moderator_user, factory_user, admin_user_token
):
    """Test that cache for one user is not affected by operations on another user"""
    user_1_id = normal_user.id
    user_2_id = moderator_user.id

    get_url_1 = f"{base_users_url}/{user_1_id}"
    get_url_2 = f"{base_users_url}/{user_2_id}"
    put_url_2 = f"{base_users_url}/{user_2_id}"

    # Cache user 1
    response_1 = await client.get(get_url_1, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Cache user 2
    response_2 = await client.get(get_url_2, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "MISS"

    # Verify both are cached
    response_1_cached = await client.get(get_url_1, headers=admin_user_token)
    assert response_1_cached.headers.get("x-api-cache") == "HIT"

    response_2_cached = await client.get(get_url_2, headers=admin_user_token)
    assert response_2_cached.headers.get("x-api-cache") == "HIT"

    # Update user 2
    update_data = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": True,
    }
    put_response = await client.put(put_url_2, headers=admin_user_token, json=update_data)
    assert put_response.status_code == 200

    # User 1 cache should still be HIT (not affected)
    response_1_after_update = await client.get(get_url_1, headers=admin_user_token)
    assert response_1_after_update.status_code == 200
    assert response_1_after_update.headers.get("x-api-cache") == "HIT"

    # User 2 cache should be MISS (invalidated)
    response_2_after_update = await client.get(get_url_2, headers=admin_user_token)
    assert response_2_after_update.status_code == 200
    assert response_2_after_update.headers.get("x-api-cache") == "MISS"


@pytest.mark.anyio
async def test_cache_invalidation_multiple_operations_same_user(
    client: AsyncClient, normal_user, factory_user, admin_user_token
):
    """Test cache invalidation through multiple operations on same user"""
    user_id = normal_user.id
    get_url = f"{base_users_url}/{user_id}"
    put_url = f"{base_users_url}/{user_id}"
    patch_disable_url = f"{base_users_url}/disable/{user_id}"

    user_token = await get_user_token(client, normal_user)

    # Initial cache
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Verify cached
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.headers.get("x-api-cache") == "HIT"

    # First update via PUT
    update_data_1 = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": True,
    }
    put_response = await client.put(put_url, headers=admin_user_token, json=update_data_1)
    assert put_response.status_code == 200

    # Should be MISS after PUT
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.headers.get("x-api-cache") == "MISS"

    # Cache again
    response_4 = await client.get(get_url, headers=admin_user_token)
    assert response_4.headers.get("x-api-cache") == "HIT"

    # Second update via PATCH
    patch_response = await client.patch(patch_disable_url, headers=user_token)
    assert patch_response.status_code == 200

    # Should be MISS after PATCH
    response_5 = await client.get(get_url, headers=admin_user_token)
    assert response_5.headers.get("x-api-cache") == "MISS"
    assert response_5.json()["is_active"] is False


# ========================
# EDGE CASES AND ERRORS
# ========================


@pytest.mark.anyio
async def test_cache_behavior_with_404_user(client: AsyncClient, random_uuid, admin_user_token):
    """Test cache behavior when user doesn't exist"""
    get_url = f"{base_users_url}/{random_uuid}"

    # First request - 404, should not be cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 404
    # 404 responses typically don't have cache headers or have short cache times

    # Second request - should still be 404
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 404
    assert response_1.json() == response_2.json()


@pytest.mark.anyio
async def test_cache_behavior_with_unauthorized_access(client: AsyncClient, normal_user, moderator_user):
    """Test cache behavior when user tries to access another user's data without permission"""
    target_user_id = moderator_user.id
    unauthorized_token = await get_user_token(client, normal_user)
    get_url = f"{base_users_url}/{target_user_id}"

    # Should return 403, not cached
    response_1 = await client.get(get_url, headers=unauthorized_token)
    assert response_1.status_code == 403

    response_2 = await client.get(get_url, headers=unauthorized_token)
    assert response_2.status_code == 403
    assert response_1.json() == response_2.json()


@pytest.mark.anyio
async def test_cache_invalidation_preserves_permissions(client: AsyncClient, normal_user, factory_user):
    """Test that cache invalidation doesn't affect authorization checks"""
    user_id = normal_user.id
    user_token = await get_user_token(client, normal_user)
    get_url = f"{base_users_url}/{user_id}"
    put_url = f"{base_users_url}/{user_id}"

    # User accesses their own data - should work and be cached
    response_1 = await client.get(get_url, headers=user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    response_2 = await client.get(get_url, headers=user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # User updates their own data - should work and invalidate cache
    update_data = {
        "email": factory_user.email,
        "username": factory_user.username,
        "is_active": True,
    }
    put_response = await client.put(put_url, headers=user_token, json=update_data)
    assert put_response.status_code == 200

    # Access after update - should be MISS and still work
    response_3 = await client.get(get_url, headers=user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    assert response_3.json()["email"] == factory_user.email


# datetime filters
@pytest.mark.anyio
async def test_get_users_with_conflicting_after_filters_should_return_422_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_after": "2024-01-01T00:00:00",
        "created_on_or_after": "2024-01-02T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "CONFLICTING_DATE_FILTERS" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_users_with_conflicting_before_filters_should_return_422_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_before": "2024-12-01T00:00:00",
        "created_on_or_before": "2024-12-02T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "CONFLICTING_DATE_FILTERS" in response.json()["detail"]
    assert "created_before and created_on_or_before" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_users_with_invalid_date_range_should_return_422_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_after": "2024-12-01T00:00:00",
        "created_before": "2024-01-01T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "INVALID_DATE_RANGE" in response.json()["detail"]
    assert "Start date must be before end date" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_users_with_valid_date_range_after_before_should_return_200_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_after": "2024-01-01T00:00:00",
        "created_before": "2024-12-31T23:59:59",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()
    assert "metadata" in response.json()


@pytest.mark.anyio
async def test_get_users_with_valid_date_range_on_or_after_on_or_before_should_return_200_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_on_or_after": "2024-01-01T00:00:00",
        "created_on_or_before": "2024-12-31T23:59:59",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()
    assert "metadata" in response.json()


@pytest.mark.anyio
async def test_get_users_with_mixed_valid_date_range_should_return_200_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_on_or_after": "2024-01-01T00:00:00",
        "created_before": "2024-12-31T23:59:59",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()
    assert "metadata" in response.json()


@pytest.mark.anyio
async def test_get_users_with_mixed_invalid_date_range_should_return_422_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {
        "created_after": "2024-12-01T00:00:00",
        "created_on_or_before": "2024-01-01T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "INVALID_DATE_RANGE" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_users_with_only_created_after_should_return_200_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {"created_after": "2024-01-01T00:00:00", "page": 1, "page_size": 10}

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.anyio
async def test_get_users_with_only_created_before_should_return_200_GET(
    session, client, batch_setup_users, moderator_user_token
):
    query_params = {"created_before": "2024-12-31T23:59:59", "page": 1, "page_size": 10}

    response = await client.get(
        f"{base_users_url}?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()
