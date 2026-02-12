from datetime import datetime
from datetime import timezone

import httpx
from fastapi import APIRouter

from app.core.telemetry import logger
from app.schemas.base_schema import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def ping():
    logger.info("Healthcheck triggered successfully")
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/password")
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
        # raise HTTPException(status_code=502, detail="Failed to fetch external password")
