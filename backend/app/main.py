"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.services.storage.factory import create_storage_service


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.state.storage_service = create_storage_service(settings)
    configure_cors(app)
    register_routers(app)

    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware if origins are defined."""

    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in origins],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )


def register_routers(app: FastAPI) -> None:
    """Register API routers."""

    app.include_router(api_router, prefix=settings.api_prefix)


__all__ = ["create_app"]
