from fastapi import APIRouter

from app.core.dependencies import AuthServiceDependency
from app.core.dependencies import CurrentUserDependency
from app.core.telemetry import logger
from app.schemas.auth_schema import SignIn
from app.schemas.auth_schema import SignInResponse
from app.schemas.auth_schema import SignUp
from app.schemas.user_schema import User as UserSchema

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/sign-in", response_model=SignInResponse)
async def sign_in(user_info: SignIn, service: AuthServiceDependency):
    extra = {
        "user_id": "usr_123",
        "email": user_info.email,
        "provider": "local",
        "environment": "dev",
        "region": "sa-east-1",
        "service_name": "auth-api",
        "service_version": "1.2.0",
        "request_id": "req_abc123",
        "trace_id": "trace_xyz789",
        "session_id": "sess_456",
        "ip_address": "192.168.1.10",
        "user_agent": "Mozilla/5.0",
        "tenant_id": "org_999",
        "feature_flag": True,
        "login_attempt": 3,
        "latency_ms": 182.4,
        "db_query_count": 7,
        "cache_hit": False,
        "http_method": "POST",
        "http_route": "/auth/sign-in",
        "http_status_code": 200,
        "device_type": "desktop",
        "country": "BR",
        "state": "SP",
        "city": "Sao Paulo",
        "plan": "enterprise",
        "roles": ["admin", "billing"],
        "metadata": {
            "source": "web",
            "campaign": "summer-sale",
            "experiment": "login-v2",
        },
        "tags": ["auth", "signin", "critical-flow"],
    }
    logger.debug("DEBUG sign-in", extra=extra)
    logger.info("INFO sign-in", extra=extra)
    logger.warning("WARN sign-in", extra=extra)
    logger.error("ERROR sign-in", extra=extra)
    logger.critical("CRITICAL sign-in", extra=extra)

    return await service.sign_in(user_info)


@router.post("/sign-up", status_code=201, response_model=UserSchema)
async def sign_up(user_info: SignUp, service: AuthServiceDependency):
    logger.info("POST /auth/sign-up - email=%s", user_info.email)
    return await service.sign_up(user_info)


@router.post("/refresh_token")
async def refresh_token(current_user: CurrentUserDependency, service: AuthServiceDependency):
    logger.info("POST /auth/refresh_token - user_id=%s", current_user.id)
    return await service.refresh_token(current_user)


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: CurrentUserDependency):
    logger.info("GET /auth/me - user_id=%s", current_user.id)
    return current_user
