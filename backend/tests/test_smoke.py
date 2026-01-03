"""Smoke tests to verify the application starts correctly."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def test_create_app_returns_fastapi_instance():
    """Verify create_app() returns a FastAPI instance without errors."""
    from app.main import create_app

    app = create_app()
    assert isinstance(app, FastAPI)
    assert "Circuit Scope" in app.title


def test_settings_load_correctly():
    """Verify settings can be loaded from environment."""
    from app.core.config import Settings

    settings = Settings()
    assert settings.app_name is not None
    assert settings.api_prefix is not None


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok():
    """Verify the health endpoint returns status ok."""
    from app.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
