from datetime import datetime
from datetime import timezone

import httpx
from fastapi import APIRouter

from app.core.exceptions import http_errors
from app.core.telemetry import logger

router = APIRouter(prefix="/passwords", tags=["Password"])


@router.get("/")
async def get_password():
    logger.info("Password fetch triggered")

    url = "https://password.gabrielcarvalho.dev/v1/"
    params = {
        "password_length": 12,
        "quantity": 1,
        "has_punctuation": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        password = data["data"][0]

        return {
            "status": "ok",
            "password": password,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except httpx.HTTPError as e:
        logger.error(f"Error fetching password: {str(e)}")
        raise http_errors.bad_request("Error while fetching the API")
