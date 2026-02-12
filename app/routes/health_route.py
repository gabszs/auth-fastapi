from datetime import datetime
from datetime import timezone

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
