from urllib.parse import urlencode
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.schemas.api_key_schema import ApiKeySchema
from tests.helpers import get_token_by_user_id
from tests.helpers import validate_datetime

# Configuration for this endpoint
BASE_URL = "/v1/api-key"
MODEL_FACTORY = "ApiKeyFactory"  # Nome da factory no conftest
MODEL_SCHEMA = ApiKeySchema
FIXTURE_NAME = "api_key"  # Nome do fixture no conftest

# Standard datetime params for search metadata
datetime_params = {
    "created_after": None,
    "created_before": None,
    "created_on_or_after": None,
    "created_on_or_before": None,
}


# =====================
# GET LIST TESTS
# =====================


@pytest.mark.anyio
async def test_get_all_api_keys_should_return_200_OK_GET(
    session,
    client,
    default_search_options,
    multiple_api_key,
    moderator_user_token,
):
    """Test getting all api tokens with default search options"""
    expected_length = len(multiple_api_key)

    response = await client.get(
        f"{BASE_URL}/?{urlencode(default_search_options)}",
        headers=moderator_user_token,
    )
    response_json = response.json()
    api_keys_json = response_json["data"]

    assert response.status_code == 200
    assert len(api_keys_json) == expected_length
    assert (
        response_json["search_metadata"] == default_search_options | {"total_count": expected_length} | datetime_params
    )

    # Validate basic fields including user_id
    assert all(
        [
            api_key.get("name") and api_key.get("token") and api_key.get("id") and api_key.get("user_id")
            for api_key in api_keys_json
        ]
    )

    # Validate datetime fields
    assert all([validate_datetime(api_key["created_at"]) for api_key in api_keys_json])
    assert all([validate_datetime(api_key["updated_at"]) for api_key in api_keys_json])


@pytest.mark.anyio
async def test_get_all_api_keys_with_page_size_should_return_200_OK_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test getting api tokens with pagination"""
    query_find_parameters = {"ordering": "name", "page": 1, "page_size": 5}

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_find_parameters)}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert len(response_json["data"]) <= 5
    assert response_json["search_metadata"]["page_size"] == 5
    assert response_json["search_metadata"]["page"] == 1

    # Validate datetime fields
    assert all([validate_datetime(api_key["created_at"]) for api_key in response_json["data"]])
    assert all([validate_datetime(api_key["updated_at"]) for api_key in response_json["data"]])


@pytest.mark.anyio
async def test_get_all_api_keys_with_pagination_should_return_200_OK_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test getting api tokens with specific page"""
    page_size = 3
    page = 2
    ordering = "name"
    query_find_parameters = {
        "ordering": ordering,
        "page": page,
        "page_size": page_size,
    }

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_find_parameters)}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert len(response_json["data"]) <= page_size
    assert response_json["search_metadata"]["page"] == page
    assert response_json["search_metadata"]["page_size"] == page_size

    # Validate datetime fields
    assert all([validate_datetime(api_key["created_at"]) for api_key in response_json["data"]])
    assert all([validate_datetime(api_key["updated_at"]) for api_key in response_json["data"]])


# =====================
# GET BY ID TESTS
# =====================


@pytest.mark.anyio
async def test_get_api_key_by_id_should_return_200_OK_GET(session, client, api_key, moderator_user_token):
    """Test getting api token by ID"""
    response = await client.get(
        f"{BASE_URL}/{api_key.id}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == api_key.id
    assert response_json["name"] == api_key.name
    assert response_json["token"] == api_key.token
    assert response_json["is_active"] == api_key.is_active
    assert UUID(response_json["user_id"]) == api_key.user_id

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_get_api_key_by_id_should_return_404_NOT_FOUND_GET(session, random_uuid, client, moderator_user_token):
    """Test getting non-existent api token by ID"""
    response = await client.get(
        f"{BASE_URL}/{random_uuid}",
        headers=moderator_user_token,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}


@pytest.mark.anyio
async def test_get_api_key_by_id_same_user_should_return_200_OK_GET(session, client, api_key):
    """Test getting api token by ID when user owns the token"""
    token = await get_token_by_user_id(api_key.user_id, client, session)
    response = await client.get(
        f"{BASE_URL}/{api_key.id}",
        headers=token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == api_key.id
    assert UUID(response_json["user_id"]) == api_key.user_id


# =====================
# CREATE TESTS
# =====================


@pytest.mark.anyio
async def test_create_api_key_should_return_422_unprocessable_entity_POST(client, normal_user_token):
    """Test creating api token without required fields"""
    response = await client.post(f"{BASE_URL}/", headers=normal_user_token)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_api_key_should_return_201_POST(client, session, factory_api_key, user_with_token):
    """Test creating api token with valid data"""
    api_key_data = {"name": factory_api_key.name, "user_id": str(user_with_token.id)}

    response = await client.post(f"{BASE_URL}/", json=api_key_data, headers=user_with_token.token)
    response_json = response.json()

    assert response.status_code == 201
    assert UUID(response_json["id"])
    assert response_json["name"] == factory_api_key.name
    assert response_json["token"].startswith("apk_")
    assert response_json["is_active"] is True
    assert UUID(response_json["user_id"]) == user_with_token.id

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_create_api_key_with_custom_name_should_return_201_POST(client, session, user_with_token):
    """Test creating api token with custom name"""
    custom_name = "My Custom API Token"
    api_key_data = {"name": custom_name, "user_id": str(user_with_token.id)}

    response = await client.post(f"{BASE_URL}/", json=api_key_data, headers=user_with_token.token)
    response_json = response.json()

    assert response.status_code == 201
    assert response_json["name"] == custom_name
    assert response_json["token"].startswith("apk_")
    assert response_json["is_active"] is True


# =====================
# UPDATE TESTS
# =====================


@pytest.mark.anyio
async def test_update_api_key_should_return_200_OK_PUT(session, client, factory_api_key, api_key, moderator_user_token):
    """Test updating api token with valid data"""
    update_data = {
        "name": "Updated Token Name",
        "is_active": False,
    }

    response = await client.put(
        f"{BASE_URL}/{api_key.id}",
        headers=moderator_user_token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])

    # Verify all fields were updated (except user_id and token which shouldn't change)
    assert response_json["name"] == update_data["name"]
    assert response_json["is_active"] == update_data["is_active"]

    # Ensure user_id and token remain unchanged
    assert UUID(response_json["user_id"]) == api_key.user_id
    assert response_json["token"] == api_key.token


@pytest.mark.anyio
async def test_update_api_key_same_user_should_return_200_OK_PUT(session, client, factory_api_key, api_key):
    """Test updating api token when user owns the token"""
    token = await get_token_by_user_id(api_key.user_id, client, session)
    update_data = {
        "name": "My Updated Token",
        "is_active": False,
    }

    response = await client.put(
        f"{BASE_URL}/{api_key.id}",
        headers=token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    # Verify fields were updated
    assert response_json["name"] == update_data["name"]
    assert response_json["is_active"] == update_data["is_active"]


@pytest.mark.anyio
async def test_update_api_key_only_name_should_return_200_OK_PUT(session, client, api_key, moderator_user_token):
    """Test updating only the name field"""
    update_data = {
        "name": "New Token Name Only",
    }

    response = await client.put(
        f"{BASE_URL}/{api_key.id}",
        headers=moderator_user_token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert response_json["name"] == update_data["name"]
    # Ensure is_active remains unchanged
    assert response_json["is_active"] == api_key.is_active


@pytest.mark.anyio
async def test_update_api_key_only_is_active_should_return_200_OK_PUT(session, client, api_key, moderator_user_token):
    """Test updating only the is_active field"""
    update_data = {
        "is_active": not api_key.is_active,
    }

    response = await client.put(
        f"{BASE_URL}/{api_key.id}",
        headers=moderator_user_token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert response_json["is_active"] == update_data["is_active"]
    # Ensure name remains unchanged
    assert response_json["name"] == api_key.name


@pytest.mark.anyio
async def test_update_api_key_should_return_404_NOT_FOUND_PUT(
    session, client, factory_api_key, random_uuid, moderator_user_token
):
    """Test updating non-existent api token"""
    update_data = {
        "name": "Non-existent Token",
        "is_active": False,
    }

    response = await client.put(
        f"{BASE_URL}/{random_uuid}",
        headers=moderator_user_token,
        json=update_data,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}


# =====================
# DELETE TESTS
# =====================


@pytest.mark.anyio
async def test_delete_api_key_should_return_204_OK_DELETE(session, client, api_key, admin_user_token):
    """Test deleting api token with admin permissions"""
    response = await client.delete(f"{BASE_URL}/{api_key.id}", headers=admin_user_token)

    # Verify deletion
    get_response = await client.get(
        f"{BASE_URL}/{api_key.id}",
        headers=admin_user_token,
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_api_key_same_user_should_return_204_OK_DELETE(session, client, api_key):
    """Test deleting api token when user owns the token (allow_same_id=True)"""
    token = await get_token_by_user_id(api_key.user_id, client, session)

    response = await client.delete(f"{BASE_URL}/{api_key.id}", headers=token)

    # Verify deletion
    get_response = await client.get(
        f"{BASE_URL}/{api_key.id}",
        headers=token,
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_api_key_should_return_404_NOT_FOUND_DELETE(session, random_uuid, client, admin_user_token):
    """Test deleting non-existent api token"""
    response = await client.delete(
        f"{BASE_URL}/{random_uuid}",
        headers=admin_user_token,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id: {random_uuid} not found"}


# =====================
# CACHE BEHAVIOR TESTS
# =====================


@pytest.mark.anyio
async def test_get_api_key_by_id_cache_miss_then_hit(client: AsyncClient, api_key, admin_user_token):
    """Test that first request is MISS and subsequent requests are HIT"""
    api_key_id = api_key.id
    url = f"{BASE_URL}/{api_key_id}"

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
    assert UUID(data_1["id"]) == api_key_id


@pytest.mark.anyio
async def test_get_api_key_by_id_cache_headers_present(client: AsyncClient, api_key, admin_user_token):
    """Test that cache-related headers are present"""
    api_key_id = api_key.id
    url = f"{BASE_URL}/{api_key_id}"

    response = await client.get(url, headers=admin_user_token)

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "max-age=360" in response.headers.get("cache-control", "")
    assert "etag" in response.headers
    assert response.headers.get("etag").startswith("W/")
    assert "x-api-cache" in response.headers


@pytest.mark.anyio
async def test_cache_invalidation_after_put_update(client: AsyncClient, api_key, factory_api_key, admin_user_token):
    """Test that cache is invalidated after PUT update"""
    api_key_id = api_key.id
    url = f"{BASE_URL}/{api_key_id}"

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
        "name": "Updated Cache Test Token",
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
    assert updated_data["name"] == update_data["name"]
    assert updated_data["is_active"] == update_data["is_active"]
    assert updated_data != original_data

    # Next GET should be HIT again
    response_4 = await client.get(url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"
    assert response_4.json() == updated_data


@pytest.mark.anyio
async def test_cache_invalidation_after_delete(session, client: AsyncClient, api_key, admin_user_token):
    """Test that cache is invalidated after DELETE operation"""
    api_key_id = api_key.id
    get_url = f"{BASE_URL}/{api_key_id}"
    delete_url = f"{BASE_URL}/{api_key_id}"

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # DELETE api token
    delete_response = await client.delete(delete_url, headers=admin_user_token)
    assert delete_response.status_code == 204

    # GET after DELETE - should return 404 (api token deleted, cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 404
    assert response_3.json() == {"detail": f"Resource with id={api_key_id} not found"}


# =====================
# DATETIME FILTER TESTS
# =====================


@pytest.mark.anyio
async def test_get_api_keys_with_conflicting_after_filters_should_return_422_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test conflicting 'after' date filters"""
    query_params = {
        "created_after": "2024-01-01T00:00:00",
        "created_on_or_after": "2024-01-02T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "CONFLICTING_DATE_FILTERS" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_api_keys_with_conflicting_before_filters_should_return_422_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test conflicting 'before' date filters"""
    query_params = {
        "created_before": "2024-12-01T00:00:00",
        "created_on_or_before": "2024-12-02T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "CONFLICTING_DATE_FILTERS" in response.json()["detail"]
    assert "created_before and created_on_or_before" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_api_keys_with_invalid_date_range_should_return_422_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test invalid date range (end before start)"""
    query_params = {
        "created_after": "2024-12-01T00:00:00",
        "created_before": "2024-01-01T00:00:00",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 422
    assert "INVALID_DATE_RANGE" in response.json()["detail"]
    assert "Start date must be before end date" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_api_keys_with_valid_date_range_should_return_200_GET(
    session, client, multiple_api_key, moderator_user_token
):
    """Test valid date range filters"""
    query_params = {
        "created_after": "2024-01-01T00:00:00",
        "created_before": "2024-12-31T23:59:59",
        "page": 1,
        "page_size": 10,
    }

    response = await client.get(
        f"{BASE_URL}/?{urlencode(query_params)}",
        headers=moderator_user_token,
    )

    assert response.status_code == 200
    assert "data" in response.json()
    assert "search_metadata" in response.json()


# =====================
# AUTHORIZATION TESTS
# =====================


@pytest.mark.anyio
async def test_get_api_keys_without_auth_should_return_403_GET(client):
    """Test getting api tokens without authentication"""
    response = await client.get(f"{BASE_URL}/")

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_api_key_by_id_without_auth_should_return_403_GET(client, api_key):
    """Test getting api token by ID without authentication"""
    response = await client.get(f"{BASE_URL}/{api_key.id}")

    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_api_key_without_auth_should_return_403_POST(client):
    """Test creating api token without authentication"""
    api_key_data = {"name": "Test Token", "user_id": "550e8400-e29b-41d4-a716-446655440000"}

    response = await client.post(f"{BASE_URL}/", json=api_key_data)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_api_key_without_auth_should_return_403_PUT(client, api_key):
    """Test updating api token without authentication"""
    update_data = {
        "name": "Updated Token",
        "is_active": False,
    }

    response = await client.put(f"{BASE_URL}/{api_key.id}", json=update_data)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_delete_api_key_without_auth_should_return_403_DELETE(client, api_key):
    """Test deleting api token without authentication"""
    response = await client.delete(f"{BASE_URL}/{api_key.id}")

    assert response.status_code == 403


# =====================
# BUSINESS LOGIC TESTS
# =====================


@pytest.mark.anyio
async def test_api_key_creation_generates_correct_token_format(client, session, user_with_token):
    """Test that API token creation generates token with correct format"""
    api_key_data = {"name": "Format Test Token", "user_id": str(user_with_token.id)}

    response = await client.post(f"{BASE_URL}/", json=api_key_data, headers=user_with_token.token)
    response_json = response.json()

    assert response.status_code == 201
    # Token should start with "apk_" followed by username and ULID
    token = response_json["token"]
    assert token.startswith(f"apk_{user_with_token.username}_")
    assert len(token) > len(f"apk_{user_with_token.username}_")


@pytest.mark.anyio
async def test_api_key_creation_sets_default_values(client, session, user_with_token):
    """Test that API token creation sets correct default values"""
    api_key_data = {"name": "Default Values Test", "user_id": str(user_with_token.id)}

    response = await client.post(f"{BASE_URL}/", json=api_key_data, headers=user_with_token.token)
    response_json = response.json()

    assert response.status_code == 201
    assert response_json["is_active"] is True
    assert response_json["user_id"] == str(user_with_token.id)
