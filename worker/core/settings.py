from pathlib import Path

import toml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

load_dotenv()


def get_version_from_pyproject():
    file_path = Path(__file__).resolve().parent.parent.parent.parent / "pyproject.toml"
    data = toml.load(file_path)
    return data["project"]["version"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("dev.env", ".env"), env_file_encoding="utf-8")

    CLIENT_ID: str
    CLIENT_SECRET: str

    URL: str = "https://services-uat.bees-platform.dev/api/"
    COSMOSDB_CREDENTIAL: str = (
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
    )
    COSMOSDB_URL: str = "http://127.0.0.1:8081/"
    COSMOS_ENABLE_ENDPOINT_DISCOVERY: bool = True
    SETUP_COSMOS_DB: bool = False

    # Cosmos collections

    DATABASE_NAME: str = "ntt"
    PARTITION_KEY: str = "/distributor"
    ITEMS: str = "items"
    ACCOUNTS: str = "accounts"
    PRICES: str = "prices"
    INVENTORY: str = "inventory"
    DELIVERY_WINDOWS: str = "delivery_windows"
    REQUEST_TRACE_ID: str = "requestTraceId_ntt_Gielow"

    #### API BEES
    BEES_ENTITY_ACCOUNT: str = "ACCOUNTS"
    BEES_ENTITY_ITEMS: str = "ITEMS"
    BEES_ENTITY_PRICES: str = "PRICES"
    BEES_ENTITY_INVENTORY: str = "INVENTORY"
    BEES_ENTITY_DELIVERY_WINDOWS: str = "DELIVERY_WINDOWS"
    BEES_VERSION_API_V1: str = "v1"
    BEES_VERSION_API_V2: str = "v2"
    BEES_VERSION_API_V3: str = "v3"
    BEES_URL_V1: str = "v1/data-ingestion-relay-service/v1"

    # REDIS
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379

    # API CONFIG SETTINGS
    TITLE: str = "NTT"
    DESCRIPTION: str = "API Integração"
    API_VERSION: str = get_version_from_pyproject()

    # open-telemetry, please do not fill
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_EXPORTER_OTLP_INSECURE: str = ""
    OTEL_LOGS_EXPORTER: str = ""
    OTEL_EXPORTER_OTLP_PROTOCOL: str = ""
    OTEL_TRACES_EXPORTER: str = ""
    OTEL_SERVICE_NAME: str = ""


settings = Settings()
