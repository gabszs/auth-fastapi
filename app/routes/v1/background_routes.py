from fastapi import APIRouter
from fastapi import BackgroundTasks

from app.core.telemetry import instrument
from app.core.telemetry import logger
from app.schemas.base_schema import Message

router = APIRouter(prefix="/background", tags=["Background"])


@instrument
def write_log(email: str):
    logger.info(f"Email task succesifully received, email: {email}", extra={"email": email})


@router.post("/send-email/", response_model=Message)
async def send_email(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, email)

    return Message(detail=f"Email will be sent to {email}")
