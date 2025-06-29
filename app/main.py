import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

from app.core.database import sessionmanager
from app.core.settings import settings
from app.routes import app_routes


def init_app(init_db=True):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logging.getLogger("opentelemetry").propagate = False
    # logger.addHandler(logging.StreamHandler()) # use this to print the logs in the console

    lifespan = None

    if init_db:

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            sessionmanager.init(settings.DATABASE_URL)
            redis = aioredis.from_url(settings.REDIS_URL)
            FastAPICache.init(
                RedisBackend(redis),
                # prefix=settings.CACHE_PREFIX,
                expire=settings.CACHE_TTS,
                cache_status_header=settings.CACHE_STATUS_HEADER,
            )

            logger.info(f"{settings.PROJECT_NAME} initialization started.")
            # from icecream import ic;ic(settings)
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
    app.include_router(app_routes)

    return app


app = init_app()
