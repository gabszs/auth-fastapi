from fastapi import APIRouter
from fastapi import BackgroundTasks
from opentelemetry import trace

from app.core.telemetry import instrument
from app.core.telemetry import logger
from app.schemas.base_schema import Message

router = APIRouter(prefix="/background", tags=["Background"])


@instrument
def write_log(email: str):
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x")

    logger.info(f"TraceId caught: {trace_id}")
    logger.info(f"Email task succesifully received, email: {email}", extra={"email": email})


@router.post("/send-email/", response_model=Message)
async def send_email(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, email)

    return Message(detail=f"Email will be sent to {email}")
