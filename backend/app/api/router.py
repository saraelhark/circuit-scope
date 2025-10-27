"""API router registration."""

from fastapi import APIRouter

from .routes import health, projects, reviews

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

__all__ = ["api_router"]
