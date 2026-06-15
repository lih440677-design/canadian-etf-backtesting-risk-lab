from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Canadian ETF Backtesting & Risk Lab API",
        description=(
            "Backtesting API for Canadian stocks and ETFs. "
            "Educational and research use only; not investment advice."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/api")
    return app


app = create_app()

