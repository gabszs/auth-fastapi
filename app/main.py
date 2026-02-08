import logging
from contextlib import asynccontextmanager

import pyroscope
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from opentelemetry import trace
from pyroscope.otel import PyroscopeSpanProcessor
from redis import asyncio as aioredis

from app.core.database import sessionmanager
from app.core.middleware import OtelMiddleware
from app.core.middleware import PyroscopeMiddleware
from app.core.settings import settings
from app.core.telemetry import logger
from app.routes import app_routes

pyroscope.configure(
    application_name=settings.OTEL_SERVICE_NAME,
    server_address=settings.PYROSCOPE_SERVER_ADDRESS,
    basic_auth_username=settings.PYROSCOPE_BASIC_AUTH_USERNAME,
    basic_auth_password=settings.PYROSCOPE_BASIC_AUTH_PASSWORD,
    tags={"service.namespace": settings.OTEL_SERVICE_NAMESPACE},
)

provider = trace.get_tracer_provider()
provider.add_span_processor(PyroscopeSpanProcessor())


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.setLevel(settings.OTEL_PYTHON_LOG_LEVEL)
    logging.getLogger("opentelemetry").propagate = False
    logger.info(f"{settings.OTEL_SERVICE_NAME} initialization started.")
    yield
    logger.info(f"{settings.OTEL_SERVICE_NAME} shutdown completed.")


def init_app(init_db=True):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.getLogger("opentelemetry").propagate = False

    if init_db:

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            sessionmanager.init(settings.DATABASE_URL)
            redis = aioredis.from_url(settings.REDIS_URL)
            FastAPICache.init(
                RedisBackend(redis),
                prefix=settings.CACHE_PREFIX,
                expire=settings.CACHE_TTS,
                cache_status_header=settings.CACHE_STATUS_HEADER,
            )

            logger.info(f"{settings.PROJECT_NAME} initialization started.")
            yield
            logger.info(f"{settings.PROJECT_NAME} shutdown completed.")
            if sessionmanager._engine is not None:
                await sessionmanager.close()

    app = FastAPI(
        title=settings.title,
        description=settings.description,
        contact=settings.contact,
        summary=settings.summary,
        lifespan=lifespan,
    )

    app.add_middleware(PyroscopeMiddleware)
    app.add_middleware(OtelMiddleware)

    app.include_router(app_routes)

    return app


app = init_app()
