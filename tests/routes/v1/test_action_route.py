from urllib.parse import urlencode
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.schemas.action_schema import ActionSchema
from tests.helpers import get_token_by_user_id
from tests.helpers import validate_datetime

# Configuration for this endpoint
BASE_URL = "/v1/action"
MODEL_FACTORY = "ActionFactory"  # Nome da factory no conftest
MODEL_SCHEMA = ActionSchema
FIXTURE_NAME = "action"  # Nome do fixture no conftest

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
async def test_get_all_actions_should_return_200_OK_GET(
    session,
    client,
    default_search_options,
    multiple_action,
    moderator_user_token,
):
    """Test getting all actions with default search options"""
    expected_length = len(multiple_action)

    response = await client.get(
        f"{BASE_URL}/?{urlencode(default_search_options)}",
        headers=moderator_user_token,
    )
    response_json = response.json()
    actions_json = response_json["data"]

    assert response.status_code == 200
    assert len(actions_json) == expected_length
    assert (
        response_json["search_metadata"] == default_search_options | {"total_count": expected_length} | datetime_params
    )

    # Validate basic fields including user_id
    assert all(
        [
            action.get("name") and action.get("url") and action.get("id") and action.get("user_id")
            for action in actions_json
        ]
    )

    # Validate datetime fields
    assert all([validate_datetime(action["created_at"]) for action in actions_json])
    assert all([validate_datetime(action["updated_at"]) for action in actions_json])


@pytest.mark.anyio
async def test_get_all_actions_with_page_size_should_return_200_OK_GET(
    session, client, multiple_action, moderator_user_token
):
    """Test getting actions with pagination"""
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
    assert all([validate_datetime(action["created_at"]) for action in response_json["data"]])
    assert all([validate_datetime(action["updated_at"]) for action in response_json["data"]])


@pytest.mark.anyio
async def test_get_all_actions_with_pagination_should_return_200_OK_GET(
    session, client, multiple_action, moderator_user_token
):
    """Test getting actions with specific page"""
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
    assert all([validate_datetime(action["created_at"]) for action in response_json["data"]])
    assert all([validate_datetime(action["updated_at"]) for action in response_json["data"]])


# =====================
# GET BY ID TESTS
# =====================


@pytest.mark.anyio
async def test_get_action_by_id_should_return_200_OK_GET(session, client, action, moderator_user_token):
    """Test getting action by ID"""
    response = await client.get(
        f"{BASE_URL}/{action.id}",
        headers=moderator_user_token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == action.id
    assert response_json["name"] == action.name
    assert response_json["url"] == action.url
    assert response_json["path_url"] == action.path_url
    assert response_json["body_version"] == action.body_version
    assert response_json["schedule"] == action.schedule
    assert UUID(response_json["user_id"]) == action.user_id

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


@pytest.mark.anyio
async def test_get_action_by_id_should_return_404_NOT_FOUND_GET(session, random_uuid, client, moderator_user_token):
    """Test getting non-existent action by ID"""
    response = await client.get(
        f"{BASE_URL}/{random_uuid}",
        headers=moderator_user_token,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}


@pytest.mark.anyio
async def test_get_action_by_id_same_user_should_return_200_OK_GET(session, client, action):
    """Test getting action by ID when user owns the action"""
    token = await get_token_by_user_id(action.user_id, client, session)
    response = await client.get(
        f"{BASE_URL}/{action.id}",
        headers=token,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert UUID(response_json["id"]) == action.id
    assert UUID(response_json["user_id"]) == action.user_id


# @pytest.mark.anyio
# async def test_get_action_by_id_different_user_should_return_403_FORBIDDEN_GET(
#     session, client, action, normal_user_token
# ):
#     """Test getting action by ID when user doesn't own the action"""
#     response = await client.get(
#         f"{BASE_URL}/{action.id}",
#         headers=normal_user_token,
#     )

#     assert response.status_code == 403
#     assert response.json() == {"detail": "Not enough permissions"}


# =====================
# CREATE TESTS
# =====================


@pytest.mark.anyio
async def test_create_action_should_return_422_unprocessable_entity_POST(client, normal_user_token):
    """Test creating action without required fields"""
    response = await client.post(f"{BASE_URL}/", headers=normal_user_token)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_action_should_return_201_POST(client, session, factory_action, user_with_token):
    """Test creating action with valid data"""
    action_data = {
        "name": factory_action.name,
        "url": factory_action.url,
        "path_url": factory_action.path_url,
        "body_version": factory_action.body_version,
        "schedule": factory_action.schedule,
    }

    response = await client.post(f"{BASE_URL}/", json=action_data, headers=user_with_token.token)
    response_json = response.json()

    assert response.status_code == 201
    assert UUID(response_json["id"])
    assert response_json["name"] == factory_action.name
    assert response_json["url"] == factory_action.url
    assert response_json["path_url"] == factory_action.path_url
    assert response_json["body_version"] == factory_action.body_version
    assert response_json["schedule"] == factory_action.schedule
    assert UUID(response_json["user_id"]) == user_with_token.id

    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])


# =====================
# UPDATE TESTS
# =====================


@pytest.mark.anyio
async def test_update_action_should_return_200_OK_PUT(session, client, factory_action, action, moderator_user_token):
    """Test updating action with valid data"""
    update_data = {
        "name": factory_action.name,
        "url": factory_action.url,
        "path_url": factory_action.path_url,
        "body_version": factory_action.body_version,
        "schedule": factory_action.schedule,
    }

    response = await client.put(
        f"{BASE_URL}/{action.id}",
        headers=moderator_user_token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    assert validate_datetime(response_json["created_at"])
    assert validate_datetime(response_json["updated_at"])

    # Verify all fields were updated (except user_id which shouldn't change)
    for key, value in update_data.items():
        assert response_json[key] == value

    # Ensure user_id remains unchanged
    assert UUID(response_json["user_id"]) == action.user_id


@pytest.mark.anyio
async def test_update_action_same_user_should_return_200_OK_PUT(session, client, factory_action, action):
    """Test updating action when user owns the action"""
    token = await get_token_by_user_id(action.user_id, client, session)
    update_data = {
        "name": factory_action.name,
        "url": factory_action.url,
        "path_url": factory_action.path_url,
    }

    response = await client.put(
        f"{BASE_URL}/{action.id}",
        headers=token,
        json=update_data,
    )
    response_json = response.json()

    assert response.status_code == 200
    # Verify fields were updated
    for key, value in update_data.items():
        assert response_json[key] == value


# @pytest.mark.anyio
# async def test_update_action_different_user_should_return_403_FORBIDDEN_PUT(
#     session, client, factory_action, action, normal_user_token
# ):
#     """Test updating action when user doesn't own the action"""
#     update_data = {
#         "name": factory_action.name,
#         "url": factory_action.url,
#     }

#     response = await client.put(
#         f"{BASE_URL}/{action.id}",
#         headers=normal_user_token,
#         json=update_data,
#     )

#     assert response.status_code == 403
#     assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_update_action_should_return_404_NOT_FOUND_PUT(
    session, client, factory_action, random_uuid, moderator_user_token
):
    """Test updating non-existent action"""
    update_data = {
        "name": factory_action.name,
        "url": factory_action.url,
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
async def test_delete_action_should_return_204_OK_DELETE(session, client, action, admin_user_token):
    """Test deleting action with admin permissions"""
    response = await client.delete(f"{BASE_URL}/{action.id}", headers=admin_user_token)

    # Verify deletion
    get_response = await client.get(
        f"{BASE_URL}/{action.id}",
        headers=admin_user_token,
    )

    assert response.status_code == 204
    assert get_response.status_code == 404


# @pytest.mark.anyio
# async def test_delete_action_should_return_403_FORBIDDEN_DELETE(session, client, action, moderator_user_token):
#     """Test deleting action without admin permissions"""
#     response = await client.delete(
#         f"{BASE_URL}/{action.id}",
#         headers=moderator_user_token,
#     )

#     assert response.status_code == 403
#     assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_delete_action_should_return_404_NOT_FOUND_DELETE(session, random_uuid, client, admin_user_token):
    """Test deleting non-existent action"""
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
async def test_get_action_by_id_cache_miss_then_hit(client: AsyncClient, action, admin_user_token):
    """Test that first request is MISS and subsequent requests are HIT"""
    action_id = action.id
    url = f"{BASE_URL}/{action_id}"

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
    assert UUID(data_1["id"]) == action_id


@pytest.mark.anyio
async def test_get_action_by_id_cache_headers_present(client: AsyncClient, action, admin_user_token):
    """Test that cache-related headers are present"""
    action_id = action.id
    url = f"{BASE_URL}/{action_id}"

    response = await client.get(url, headers=admin_user_token)

    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "max-age=360" in response.headers.get("cache-control", "")
    assert "etag" in response.headers
    assert response.headers.get("etag").startswith("W/")
    assert "x-api-cache" in response.headers


@pytest.mark.anyio
async def test_cache_invalidation_after_put_update(client: AsyncClient, action, factory_action, admin_user_token):
    """Test that cache is invalidated after PUT update"""
    action_id = action.id
    url = f"{BASE_URL}/{action_id}"

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
        "name": factory_action.name,
        "url": factory_action.url,
        "path_url": factory_action.path_url,
    }

    put_response = await client.put(url, headers=admin_user_token, json=update_data)
    assert put_response.status_code == 200

    # GET after PUT - should be MISS (cache invalidated)
    response_3 = await client.get(url, headers=admin_user_token)
    assert response_3.status_code == 200
    assert response_3.headers.get("x-api-cache") == "MISS"
    updated_data = response_3.json()

    # Verify data was actually updated
    assert updated_data["name"] == factory_action.name
    assert updated_data["url"] == factory_action.url
    assert updated_data["path_url"] == factory_action.path_url
    assert updated_data != original_data

    # Next GET should be HIT again
    response_4 = await client.get(url, headers=admin_user_token)
    assert response_4.status_code == 200
    assert response_4.headers.get("x-api-cache") == "HIT"
    assert response_4.json() == updated_data


@pytest.mark.anyio
async def test_cache_invalidation_after_delete(session, client: AsyncClient, action, admin_user_token):
    """Test that cache is invalidated after DELETE operation"""
    action_id = action.id
    get_url = f"{BASE_URL}/{action_id}"
    delete_url = f"{BASE_URL}/{action_id}"

    # First GET - should be MISS and cached
    response_1 = await client.get(get_url, headers=admin_user_token)
    assert response_1.status_code == 200
    assert response_1.headers.get("x-api-cache") == "MISS"

    # Second GET - should be HIT
    response_2 = await client.get(get_url, headers=admin_user_token)
    assert response_2.status_code == 200
    assert response_2.headers.get("x-api-cache") == "HIT"

    # DELETE action
    delete_response = await client.delete(delete_url, headers=admin_user_token)
    assert delete_response.status_code == 204

    # GET after DELETE - should return 404 (action deleted, cache invalidated)
    response_3 = await client.get(get_url, headers=admin_user_token)
    assert response_3.status_code == 404
    assert response_3.json() == {"detail": f"Resource with id={action_id} not found"}


# =====================
# DATETIME FILTER TESTS
# =====================


@pytest.mark.anyio
async def test_get_actions_with_conflicting_after_filters_should_return_422_GET(
    session, client, multiple_action, moderator_user_token
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
async def test_get_actions_with_conflicting_before_filters_should_return_422_GET(
    session, client, multiple_action, moderator_user_token
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
async def test_get_actions_with_invalid_date_range_should_return_422_GET(
    session, client, multiple_action, moderator_user_token
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
async def test_get_actions_with_valid_date_range_should_return_200_GET(
    session, client, multiple_action, moderator_user_token
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
# UPLOAD FILE TESTS
# =====================


@pytest.mark.anyio
async def test_upload_file_to_action_should_return_200_OK_POST(session, client, action):
    """Test uploading file to action owned by user"""
    token = await get_token_by_user_id(action.user_id, client, session)
    file_content = b"test file content"
    files = {"file": ("test.yaml", file_content, "application/x-yaml")}  # CORRIGIDO

    response = await client.post(
        f"{BASE_URL}/{action.id}/upload",
        headers=token,
        files=files,
    )

    assert response.status_code == 200
    response_json = response.json()
    assert UUID(response_json["id"]) == action.id


# @pytest.mark.anyio
# async def test_upload_file_to_action_different_user_should_return_403_FORBIDDEN_POST(
#     session, client, action, normal_user_token
# ):
#     """Test uploading file to action not owned by user"""
#     file_content = b"test file content"
#     files = {"file": ("test.txt", file_content, "text/plain")}

#     response = await client.post(
#         f"{BASE_URL}/{action.id}/upload",
#         headers=normal_user_token,
#         files=files,
#     )

#     assert response.status_code == 403
#     assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.anyio
async def test_upload_file_to_nonexistent_action_should_return_404_POST(session, client, random_uuid, admin_user_token):
    """Test uploading file to non-existent action"""
    file_content = b"test file content"
    files = {"file": ("test.yaml", file_content, "application/x-yaml")}  # CORRIGIDO

    response = await client.post(
        f"{BASE_URL}/{random_uuid}/upload",
        headers=admin_user_token,
        files=files,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Resource with id={random_uuid} not found"}
