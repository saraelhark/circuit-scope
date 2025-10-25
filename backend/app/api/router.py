"""API router registration."""

from fastapi import APIRouter

from .routes import health, projects, reviews

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router)
api_router.include_router(reviews.router)

__all__ = ["api_router"]
