from fastapi import APIRouter

from app.routes.v1.auth_routes import router as auth_router
from app.routes.v1.password_routes import router as password_router
from app.routes.v1.users_routes import router as user_router

routers = APIRouter(prefix="/v1")
router_list = [auth_router, user_router, password_router]

for router in router_list:
    routers.include_router(router)

__all__ = ["routers"]
