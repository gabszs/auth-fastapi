from fastapi import APIRouter

from .action_routes import router as action_router
from .api_key_routes import router as api_key_router
from .auth_routes import router as auth_router
from .background_routes import router as background_router
from .users_routes import router as user_router
from .webhook_routes import router as webhook_router

routers = APIRouter(prefix="/v1")
router_list = [auth_router, user_router, background_router, webhook_router, api_key_router, action_router]

for router in router_list:
    routers.include_router(router)

__all__ = ["routers"]
