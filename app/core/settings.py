from typing import Dict
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "dev.env"), env_file_encoding="utf-8")

    # api envs
    CLIENT_ID: str
    CLIENT_SECRET: str

    PROJECT_NAME: str = "fastapi-auth"

    DATABASE_URL: str

    # cache settings
    REDIS_URL: str
    RABBITMQ_URL: str
    CACHE_TTS: int = 360
    CACHE_PREFIX: str = "auth-Api"
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
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: Optional[bool]
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_INSECURE: Optional[str] = None
    OTEL_LOGS_EXPORTER: Optional[str] = None
    OTEL_SERVICE_NAME: Optional[str] = None
    OTEL_EXPORTER_OTLP_PROTOCOL: Optional[str] = None

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
