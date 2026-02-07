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
    logger.info("POST /auth/sign-in - email=%s", user_info.email)
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
