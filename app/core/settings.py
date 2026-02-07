from typing import Dict
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "dev.env"), env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "fastapi-auth"

    DATABASE_URL: str

    # cache settings
    REDIS_URL: str
    CACHE_TTS: int = 360
    CACHE_PREFIX: str = "auth-api"
    CACHE_STATUS_HEADER: str = "x-api-cache"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 25

    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    TEST_DATABASE_URL: Optional[str] = None

    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-created_at"

    # open-telemetry, please do not fill
    OTEL_SERVICE_NAME: str
    OTEL_PYTHON_LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    SERVICE_OWNER_NAME: str = ""
    SERVICE_OWNER_URL: str = ""
    SERVICE_OWNER_CONTACT: str = ""
    SERVICE_OWNER_DISCORD: str = ""
    SERVICE_VERSION: str = ""
    COMMIT_HASH: str = ""
    COMMIT_BRANCH: str = ""
    DEPLOYMENT_USER: str = ""
    DEPLOYMENT_TRIGGER: str = ""

    # swagger app config settings
    title: str = "auth-Api"
    description: str = "Auth Web API with clean arch built by @GabrielCarvalho"
    contact: Dict[str, str] = {
        "name": "Gabriel Carvalho",
        "url": "https://www.linkedin.com/in/gabzsz/",
        "email": "gabriel.carvalho@huawei.com",
    }
    summary: str = (
        "WebAPI built on best market practices such as TDD, Clean Architecture, Data Validation with Pydantic V2"
    )


settings = Settings()
