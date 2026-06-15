import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    cors_origins: list[str]
    yahoo_timeout_seconds: int


@lru_cache
def get_settings() -> Settings:
    origins = os.getenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    timeout = int(os.getenv("YAHOO_TIMEOUT_SECONDS", "20"))
    return Settings(
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        yahoo_timeout_seconds=timeout,
    )

