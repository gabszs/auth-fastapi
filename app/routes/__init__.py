from fastapi import APIRouter

from app.routes.health_route import router as health_route
from app.routes.v1 import routers as v1_routers


app_routes = APIRouter()
app_routes.include_router(v1_routers)
app_routes.include_router(health_route)

__all__ = ["app_routes"]
