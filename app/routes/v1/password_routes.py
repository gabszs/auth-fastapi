import logging
from datetime import datetime
from datetime import timezone

import httpx
from fastapi import APIRouter
from tenacity import before_sleep_log
from tenacity import retry
from tenacity import retry_if_exception
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from app.core.dependencies import CurrentUserDependency
from app.core.exceptions import http_errors
from app.core.telemetry import logger

router = APIRouter(prefix="/passwords", tags=["Password"])


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=5),
    retry=retry_if_exception(httpx.RequestError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def fetch_password():
    url = "https://password.gabrielcarvalho.dev/v1/"
    params = {
        "password_length": 12,
        "quantity": 1,
        "has_punctuation": "true",
    }
    response = await httpx.get(url, params=params)
    if response.status_code >= 400:
        raise http_errors.bad_request("Error while fetching the API")
    data = response.json()

    return {
        "status": "ok",
        "password": data["data"][0],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("")
async def get_password():
    logger.info("Password fetch triggered")
    return await fetch_password()


@router.get("/protected")
async def get_protected_password(current_user: CurrentUserDependency):
    logger.info("Password fetch triggered")
    return await fetch_password()
