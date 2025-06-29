from urllib.parse import urlencode
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.schemas.action_schema import ActionSchema
from app.schemas.api_key_schema import ApiKeySchema
from app.schemas.webhook_schema import WebHookSchema
from tests.factories import ActionFactory
from tests.factories import ApiKeyFactory
from tests.factories import WebHookFactory
from tests.helpers import add_models_generic
from tests.helpers import get_token_by_user_id
from tests.helpers import validate_datetime
from tests.schemas import WebHookWithUserIdSchema

# Configuration for this endpoint
BASE_URL = "/v1/webhooks"
MODEL_FACTORY = "WebHookFactory"  # Nome da factory no conftest
MODEL_SCHEMA = WebHookSchema
FIXTURE_NAME = "webhook"  # Nome do fixture no conftest

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
async def test_get_all_webhooks_should_return_200_OK_GET(
    session,
    client,
    default_search_options,
    webhook,
    moderator_user_token,
):
    """Test getting all webhooks with default search options"""
    expected_length = 1

    response = await client.get(
        f"{BASE_URL}/?{urlencode(default_search_options)}",
        headers=moderator_user_token,
    )
    response_json = response.json()
    webhooks_json = response_json["data"]

    assert response.status_code == 200
    assert len(webhooks_json) == expected_length
    assert (
        response_json["search_metadata"] == default_search_options | {"total_count": expected_length} | datetime_params
    )

    # Validate basic fields including action_id
    assert all(
        [
            webhook.get("name")
            and webhook.get("action_id")
            and webhook.get("id")
            and webhook.get("is_active") is not None
            for webhook in webhooks_json
        ]
    )

    # Validate datetime fields
    assert all([validate_datetime(webhook["created_at"]) for webhook in webhooks_json])
    assert all([validate_datetime(webhook["updated_at"]) for webhook in webhooks_json])


@pytest.mark.anyio
async def test_get_all_webhooks_with_page_size_should_return_200_OK_GET(session, client, webhook, moderator_user_token):
    """Test getting webhooks with pagination"""
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
    assert all([validate_datetime(webhook["created_at"]) for webhook in response_json["data"]])
    assert all([validate_datetime(webhook["updated_at"]) for webhook in response_json["data"]])


@pytest.mark.anyio
async def test_get_all_webhooks_with_pagination_should_return_200_OK_GET(
    session, client, webhook, moderator_user_token
):
    """Test getting webhooks with specific page"""
    page_size = 3
    page = 1
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
    assert all([validate_datetime(webhook["created_at"]) for webhook in response_json["data"]])
    assert all([validate_datetime(webhook["updated_at"]) for webhook in response_json["data"]])


# =====================
# GET BY ID TESTS
# =====================


@pytest.mark.anyio
async def test_get_webhook_by_id_should_return_200_OK_GET(session, client, webhook, moderator_user_token):
    """Test getting webhook by ID"""
    response = await client.get(
        f"{BASE_URL}/{webhook.id}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == webhook.id
    assert response_json["name"] == webhook.name
    assert UUID(response_json["action_id"]) == webhook.action_id
    assert response_json["is_active"] == webhook.is_active

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_get_webhook_by_id_should_return_404_NOT_FOUND_GET(session, random_uuid, client, moderator_user_token):
    """Test getting non-existent webhook by ID"""
    response = await client.get(
        f"{BASE_URL}/{random_uuid}",
        headers=moderator_user_token,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}


@pytest.mark.anyio
async def test_get_webhook_by_id_same_user_should_return_200_OK_GET(session, client, webhook):
    """Test getting webhook by ID when user owns the related action"""
    token = await get_token_by_user_id(webhook.user_id, client, session)
    response = await client.get(
        f"{BASE_URL}/{webhook.id}",
        headers=token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == webhook.id
    assert UUID(response_json["action_id"]) == webhook.action_id


# =====================
# CREATE TESTS
# =====================


@pytest.mark.anyio
async def test_create_webhook_should_return_422_unprocessable_entity_POST(client, normal_user_token):
    """Test creating webhook without required fields"""
    response = await client.post(f"{BASE_URL}/", headers=normal_user_token)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_webhook_should_return_201_POST(client, session, factory_webhook, action):
    """Test creating webhook with valid data"""
    token = await get_token_by_user_id(action.user_id, client, session)
    webhook_data = {
        "name": factory_webhook.name,
        "action_id": str(action.id),
    }

    response = await client.post(f"{BASE_URL}/", json=webhook_data, headers=token)
    response_json = response.json()

    assert response.status_code == 201
    assert UUID(response_json["id"])
    assert response_json["name"] == factory_webhook.name
    assert UUID(response_json["action_id"]) == action.id
    assert response_json["is_active"] is True

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_create_webhook_for_different_user_action_should_return_404_POST(
    client, session, factory_webhook, action, normal_user_token
):
    """Test creating webhook for action not owned by user"""
    webhook_data = {
        "name": factory_webhook.name,
        "action_id": str(action.id),
    }

    response = await client.post(f"{BASE_URL}/", json=webhook_data, headers=normal_user_token)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_webhook_for_nonexistent_action_should_return_404_POST(
    client, session, factory_webhook, random_uuid, normal_user_token
):
    """Test creating webhook for non-existent action"""
    webhook_data = {
        "name": factory_webhook.name,
        "action_id": str(random_uuid),
    }

    response = await client.post(f"{BASE_URL}/", json=webhook_data, headers=normal_user_token)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# =====================
# UPDATE TESTS
# =====================


@pytest.mark.anyio
async def test_update_webhook_should_return_200_OK_PUT(session, client, factory_webhook, webhook, moderator_user_token):
    """Test updating webhook with valid data"""
    update_data = {
        "name": factory_webhook.name,
        "is_active": False,
    }

    response = await client.put(
        f"{BASE_URL}/{webhook.id}",
        headers=moderator_user_token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])

    # Verify all fields were updated
    for key, value in update_data.items():
        assert response_json[key] == value

    # Ensure action_id remains unchanged
    assert UUID(response_json["action_id"]) == webhook.action_id


@pytest.mark.anyio
async def test_update_webhook_same_user_should_return_200_OK_PUT(session, client, factory_webhook, webhook):
    """Test updating webhook when user owns the related action"""
    token = await get_token_by_user_id(webhook.user_id, client, session)
    update_data = {
        "name": factory_webhook.name,
        "is_active": False,
    }

    response = await client.put(
        f"{BASE_URL}/{webhook.id}",
        headers=token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    # Verify fields were updated
    for key, value in update_data.items():
        assert response_json[key] == value


@pytest.mark.anyio
async def test_update_webhook_should_return_404_NOT_FOUND_PUT(
    session, client, factory_webhook, random_uuid, moderator_user_token
):
    """Test updating non-existent webhook"""
    update_data = {
        "name": factory_webhook.name,
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
async def test_delete_webhook_should_return_204_OK_DELETE(session, client, webhook, admin_user_token):
    """Test deleting webhook with admin permissions"""
    response = await client.delete(f"{BASE_URL}/{webhook.id}", headers=admin_user_token)

    # Verify deletion
    get_response = await client.get(
        f"{BASE_URL}/{webhook.id}",
        headers=admin_user_token,
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_webhook_same_user_should_return_204_OK_DELETE(session, client, webhook):
    """Test deleting webhook when user owns the related action"""
    token = await get_token_by_user_id(webhook.user_id, client, session)
    response = await client.delete(f"{BASE_URL}/{webhook.id}", headers=token)

    # Verify deletion
    get_response = await client.get(
        f"{BASE_URL}/{webhook.id}",
        headers=token,
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_webhook_should_return_404_NOT_FOUND_DELETE(session, random_uuid, client, admin_user_token):
    """Test deleting non-existent webhook"""
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
async def test_get_webhook_by_id_cache_miss_then_hit(client: AsyncClient, webhook, admin_user_token):
    """Test that first request is MISS and subsequent requests are HIT"""
    webhook_id = webhook.id
    url = f"{BASE_URL}/{webhook_id}"

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
    assert UUID(data_1["id"]) == webhook_id


@pytest.mark.anyio
async def test_get_webhook_by_id_cache_headers_present(client: AsyncClient, webhook, admin_user_token):
    """Test that cache-related headers are present"""
    webhook_id = webhook.id
    url = f"{BASE_URL}/{webhook_id}"

    response = await client.get(url, headers=admin_user_token)

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "max-age=360" in response.headers.get("cache-control", "")
    assert "etag" in response.headers
    assert response.headers.get("etag").startswith("W/")
    assert "x-api-cache" in response.headers


@pytest.mark.anyio
async def test_cache_invalidation_after_put_update(client: AsyncClient, webhook, factory_webhook, admin_user_token):
    """Test that cache is invalidated after PUT update"""
    webhook_id = webhook.id
    url = f"{BASE_URL}/{webhook_id}"

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
        "name": factory_webhook.name,
        "is_active": False,
    }

    put_response = await client.put(f"{BASE_URL}/{webhook_id}", headers=admin_user_token, json=update_data)
    assert put_response.status_code == 200

    # GET after PUT - should be MISS (cache invalidated)
    response_3 = await client.get(url, headers=admin_user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    updated_data = response_3.json()

    # Verify data was actually updated
    assert updated_data["name"] == factory_webhook.name
    assert updated_data["is_active"] is False
    assert updated_data != original_data

    # Next GET should be HIT again
    response_4 = await client.get(url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"
    assert response_4.json() == updated_data


@pytest.mark.anyio
async def test_cache_invalidation_after_delete(session, client: AsyncClient, webhook, admin_user_token):
    """Test that cache is invalidated after DELETE operation"""
    webhook_id = webhook.id
    get_url = f"{BASE_URL}/{webhook_id}"
    delete_url = f"{BASE_URL}/{webhook_id}"

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # DELETE webhook
    delete_response = await client.delete(delete_url, headers=admin_user_token)
    assert delete_response.status_code == 204

    # GET after DELETE - should return 404 (webhook deleted, cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 404
    assert response_3.json() == {"detail": f"Resource with id={webhook_id} not found"}


# =====================
# DATETIME FILTER TESTS
# =====================


@pytest.mark.anyio
async def test_get_webhooks_with_conflicting_after_filters_should_return_422_GET(
    session, client, webhook, moderator_user_token
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
async def test_get_webhooks_with_conflicting_before_filters_should_return_422_GET(
    session, client, webhook, moderator_user_token
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
async def test_get_webhooks_with_invalid_date_range_should_return_422_GET(
    session, client, webhook, moderator_user_token
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
async def test_get_webhooks_with_valid_date_range_should_return_200_GET(session, client, webhook, moderator_user_token):
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
# UNIQUE CONSTRAINT TESTS
# =====================


@pytest.mark.anyio
async def test_create_webhook_duplicate_action_id_should_return_400_POST(client, session, factory_webhook, webhook):
    """Test creating webhook with duplicate action_id (unique constraint)"""
    token = await get_token_by_user_id(webhook.user_id, client, session)
    webhook_data = {
        "name": "Another Webhook Name",
        "action_id": str(webhook.action_id),  # Same action_id as existing webhook
    }

    response = await client.post(f"{BASE_URL}/", json=webhook_data, headers=token)

    # Should fail due to unique constraint on action_id
    assert response.status_code == 409


# =====================
# WEBHOOK TRIGGER TESTS
# =====================


@pytest.mark.anyio
async def test_trigger_webhook_should_return_422_missing_api_key_POST(session, client, webhook):
    """Test triggering webhook without API key header"""
    response = await client.post(f"{BASE_URL}/{webhook.id}")

    assert response.status_code == 422


@pytest.mark.anyio
async def test_trigger_webhook_should_return_403_empty_api_key_POST(session, client, webhook):
    """Test triggering webhook with empty API key header"""
    headers = {"x-api-key": ""}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 403
    assert "API key is required" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_should_return_401_invalid_api_key_POST(session, client, webhook):
    """Test triggering webhook with invalid API key"""
    headers = {"x-api-key": "invalid-api-key-token"}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 401
    assert "Invalid or inactive API key" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_should_return_401_inactive_api_key_POST(session, client, webhook, normal_user):
    """Test triggering webhook with inactive API key"""
    # Create inactive API key for the webhook owner
    inactive_api_key = await add_models_generic(
        session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id, is_active=False
    )

    headers = {"x-api-key": inactive_api_key.token}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 401
    assert "Invalid or inactive API key" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_should_return_404_nonexistent_webhook_POST(session, client, random_uuid, normal_user):
    """Test triggering non-existent webhook with valid API key"""
    # Create valid API key
    valid_api_key = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=normal_user.id)

    headers = {"x-api-key": valid_api_key.token}

    response = await client.post(f"{BASE_URL}/{random_uuid}", headers=headers)

    assert response.status_code == 404
    assert f"Resource with id={random_uuid} not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_should_return_403_different_user_api_key_POST(session, client, webhook, moderator_user):
    """Test triggering webhook with API key from different user"""
    # Create API key for different user (moderator)
    different_user_api_key = await add_models_generic(
        session, ApiKeyFactory, ApiKeySchema, index=0, user_id=moderator_user.id
    )

    headers = {"x-api-key": different_user_api_key.token}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 403
    assert "You do not have permission to access this webhook" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_should_return_202_valid_api_key_same_user_POST(session, client, webhook):
    """Test triggering webhook with valid API key from webhook owner"""
    # Create valid API key for webhook owner
    valid_api_key = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    headers = {"x-api-key": valid_api_key.token}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 202


@pytest.mark.anyio
async def test_trigger_webhook_should_return_202_multiple_valid_calls_POST(session, client, webhook):
    """Test multiple successful webhook triggers with same API key"""
    # Create valid API key for webhook owner
    valid_api_key = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    headers = {"x-api-key": valid_api_key.token}

    # First call
    response_1 = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)
    assert response_1.status_code == 202

    # Second call
    response_2 = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)
    assert response_2.status_code == 202

    # Third call
    response_3 = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)
    assert response_3.status_code == 202


@pytest.mark.anyio
async def test_trigger_webhook_case_sensitive_api_key_header_POST(session, client, webhook):
    """Test that API key header is case sensitive"""
    # Create valid API key for webhook owner
    valid_api_key = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    # Test with wrong case header
    headers = {"X-API-KEY": valid_api_key.token}  # Wrong case

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    assert response.status_code == 202  # Should fail due to missing proper header


@pytest.mark.anyio
async def test_trigger_webhook_with_multiple_api_keys_same_user_POST(session, client, webhook):
    """Test triggering webhook with different API keys from same user"""
    # Create multiple API keys for webhook owner
    api_key_1 = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    api_key_2 = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    # Test with first API key
    headers_1 = {"x-api-key": api_key_1.token}
    response_1 = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers_1)
    assert response_1.status_code == 202

    # Test with second API key
    headers_2 = {"x-api-key": api_key_2.token}
    response_2 = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers_2)
    assert response_2.status_code == 202


@pytest.mark.anyio
async def test_trigger_webhook_with_whitespace_api_key_POST(session, client, webhook):
    """Test triggering webhook with API key containing whitespace"""
    # Create valid API key for webhook owner
    valid_api_key = await add_models_generic(session, ApiKeyFactory, ApiKeySchema, index=0, user_id=webhook.user_id)

    # Test with whitespace in API key
    headers = {"x-api-key": f" {valid_api_key.token} "}

    response = await client.post(f"{BASE_URL}/{webhook.id}", headers=headers)

    # Should fail because whitespace makes it invalid
    assert response.status_code == 401
    assert "Invalid or inactive API key" in response.json()["detail"]


@pytest.mark.anyio
async def test_trigger_webhook_permission_boundary_test_POST(session, client, normal_user, moderator_user):
    """Test permission boundaries - each user can only trigger their own webhooks"""
    # Create action and webhook for normal user
    normal_user_action = await add_models_generic(session, ActionFactory, ActionSchema, index=0, user_id=normal_user.id)
    normal_user_webhook = await add_models_generic(
        session, WebHookFactory, WebHookSchema, index=0, action_id=normal_user_action.id
    )
    normal_user_webhook_extended = WebHookWithUserIdSchema(**normal_user_webhook.model_dump(), user_id=normal_user.id)

    # Create action and webhook for moderator user
    moderator_user_action = await add_models_generic(
        session, ActionFactory, ActionSchema, index=0, user_id=moderator_user.id
    )
    moderator_user_webhook = await add_models_generic(
        session, WebHookFactory, WebHookSchema, index=0, action_id=moderator_user_action.id
    )
    moderator_user_webhook_extended = WebHookWithUserIdSchema(
        **moderator_user_webhook.model_dump(), user_id=moderator_user.id
    )

    # Create API keys for both users
    normal_user_api_key = await add_models_generic(
        session, ApiKeyFactory, ApiKeySchema, index=0, user_id=normal_user.id
    )
    moderator_user_api_key = await add_models_generic(
        session, ApiKeyFactory, ApiKeySchema, index=0, user_id=moderator_user.id
    )

    # Normal user can trigger their own webhook
    headers_normal = {"x-api-key": normal_user_api_key.token}
    response_1 = await client.post(f"{BASE_URL}/{normal_user_webhook_extended.id}", headers=headers_normal)
    assert response_1.status_code == 202

    # Moderator user can trigger their own webhook
    headers_moderator = {"x-api-key": moderator_user_api_key.token}
    response_2 = await client.post(f"{BASE_URL}/{moderator_user_webhook_extended.id}", headers=headers_moderator)
    assert response_2.status_code == 202

    # Normal user CANNOT trigger moderator's webhook
    response_3 = await client.post(f"{BASE_URL}/{moderator_user_webhook_extended.id}", headers=headers_normal)
    assert response_3.status_code == 403
    assert "You do not have permission to access this webhook" in response_3.json()["detail"]

    # Moderator user CANNOT trigger normal user's webhook
    response_4 = await client.post(f"{BASE_URL}/{normal_user_webhook_extended.id}", headers=headers_moderator)
    assert response_4.status_code == 403
    assert "You do not have permission to access this webhook" in response_4.json()["detail"]
