"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.services.storage.factory import create_storage_service


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""

    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.storage_service = create_storage_service(settings)
    configure_cors(app)
    register_routers(app)

    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware if origins are defined."""

    origins = settings.cors_origins

    # In development, default to allowing local Nuxt dev origins if none are configured.
    if not origins and settings.debug:
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    if not origins:
        return

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
